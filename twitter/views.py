
import json

from django.db import IntegrityError
from django.contrib import auth
from django.http.response import HttpResponseNotAllowed
from django.shortcuts import render
from django.utils import timezone
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, JsonResponse, request
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateformat import DateFormat
from django.contrib.auth import authenticate, login as session_login, logout as session_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from .models import User, Post, Like, Retweet, Feed, Config
from .forms import SignupForm
from .utils import (
    create_new_user, bulk_insert_feed, tweet_thread, 
    update_signup_info, signup_info, missing_page,
                    )

from sawo import getContext, verifyToken

config = Config.objects.order_by('-api_key')[:1]

def index(request):
    if request.method == 'GET':
        return render(request, 'twitter/index.html', {'title':'Join Twitter'})

    return HttpResponseNotAllowed(['GET'])

def signup(request):
    if request.method == 'GET':
        context = {
            "title": 'Join Twitter',
            "form": SignupForm(initial=signup_info(request.session)),
        }
        return render(request, 'twitter/signup.html', context) 
    elif request.method == 'POST': 
        form = SignupForm(request.POST)
        if form.is_valid():
            update_signup_info(request)
            return HttpResponseRedirect(reverse('login'))
        context = {'title': 'Join Twitter','form':form}
        return render(request, 'twitter/signup.html', context) 

    return HttpResponseNotAllowed(['GET', 'POST'])

@csrf_exempt
def login(request):
    if request.method == 'GET':
        redirect_url = request.GET.get('next','')
        to_url = f"login/?next={redirect_url}" if redirect_url else "login/"
        context = {
            "title": 'Login',
            "form": SignupForm(initial=signup_info(request.session)),
            "sawo": getContext(config, to_url)
        }
        return render(request, 'twitter/login.html', context)

    elif request.method == 'POST':
        payload = json.loads(request.body)['payload']
        if verifyToken(payload):
            assert payload.get('identifier','')
            email = payload['identifier']

            new_user = request.session.get('username', None)        # Request coming from Sign Up view
            if new_user:
                create_new_user(request, email)

            user = authenticate(request, email=email)
            if user:
                session_login(request, user)
                redirect_url = request.GET.get('next','/home/')
                return JsonResponse({'redirect': redirect_url})
            else:
                return HttpResponse('Unauthorised', status=401)
            
        else:
            return HttpResponse('Unauthorised', status=401)

    return HttpResponseNotAllowed(['GET', 'POST'])

@login_required
def logout(request):
    session_logout(request)
    return HttpResponsePermanentRedirect(reverse('index'))

@login_required
def tweet_detail(request, username, id):
    if request.method == 'GET':
        try:
            tweet = Post.objects.get(id=id)
        except Post.DoesNotExist:
            return missing_page(request, type_='Tweet')

        comments = Post.objects.filter(parent_post__id=id)[:]       # Get direct comments under this post
        threads = [tweet_thread(comment, request.user) 
                        for comment in comments]      
                                                    # `tweet_thread` finds the chain of first-level comments
                                                    #  under each tweet (i.e a twitter comment thread)
        print(f"Feed finally: \n {threads}")
        context = {                                                     
            'tweet': {
                'obj': tweet,
                'liked_by_me'  : True if Like.objects.filter(user__id=request.user.id, post__id=tweet.id).exists()
                                        else False,
                'rtd_by_me'    : True if Retweet.objects.filter(user__id=request.user.id, post__id=tweet.id).exists()
                                    else False,
                'like_count': tweet.likes.count(),
                'rt_count'  : tweet.retweets.count(),
                'cmt_count' : tweet.comments.count(),
                },
            'threads': threads,
            'user': request.user
        }
        return render(request, 'twitter/tweet.html', context)

    return HttpResponseNotAllowed(['GET'])

@login_required
def profile_tweets(request, username):
    if request.method == 'GET':
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return missing_page(request, type_='User')

        offset = request.GET.get('offset', default=0)
        limit = request.GET.get('offset', default=19)
        top_tweets = Post.objects.filter(author__username=username)    \
                                .order_by('-timestamp')[offset:limit+1]
        post_data = [{'obj'     : post,
                    'liked_by_me'  : True if Like.objects.filter(user__id=user.id, post__id=post.id).exists()
                                        else False,
                    'rtd_by_me'    : True if Retweet.objects.filter(user__id=user.id, post__id=post.id).exists()
                                        else False,
                    'like_count': post.likes.count(),
                    'rt_count'  : post.retweets.count(),
                    'cmt_count' : post.comments.count(),
                    'age' : int((post.timestamp - timezone.now()).seconds/3600)
                        } for post in top_tweets]
        context = {
            'user': user,
            'post_data': post_data,
            'followed_by_current_user': request.user.followers.filter(id=user.id).exists(),
        }
        return render(request, 'twitter/profile_tweets.html', context)

    return HttpResponseNotAllowed(['GET'])

@login_required
def profile_likes(request, username):
    if request.method == 'GET':
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return missing_page(request, type_='User')

        offset = request.GET.get('offset', default=0)
        limit = request.GET.get('offset', default=20)
        liked_tweets = Like.objects.filter(user__username=username)    \
                                .select_related('post','post__author', \
                                                'post__parent_post')                  \
                                .prefetch_related('post__likes','post__retweets','post__comments')      \
                                .order_by('-post__timestamp')[offset:limit]
        post_data = [{'obj' : obj,
                    'post'     : obj.post,
                    'liked_by_me'  : True,
                    'rtd_by_me'    : True if Retweet.objects.filter(user__id=user.id, post__id=obj.post.id).exists()
                                        else False,
                    'like_count': obj.post.likes.count(),
                    'rt_count'  : obj.post.retweets.count(),
                    'cmt_count' : obj.post.comments.count(),
                    'age' : int((obj.post.timestamp - timezone.now()).seconds/3600)
                        } for obj in liked_tweets]
        context = {
            'user': user,
            'post_data': post_data,
            'followed_by_current_user': request.user.followers.filter(id=user.id).exists(),
        }
        return render(request, 'twitter/profile_likes.html', context)

    return HttpResponseNotAllowed(['GET'])

@login_required
def create_tweet(request):
    if request.method == 'GET':
        request.session['success_url'] = request.META['HTTP_REFERER']
        return render(request, 'twitter/tweet_form.html')

    elif request.method == 'POST':
        post = Post.objects.create(author=request.user, content=request.POST['content'])
        bulk_insert_feed(post=post,
                         activity_type="TW",
                         actor=request.user,
                         batch_size=100)             # Update Feed table for all of the user's followers
        success_url = request.session.pop('success_url', reverse('home'))
        return HttpResponseRedirect(success_url)
    
    return HttpResponseNotAllowed(['GET', 'POST'])

@csrf_exempt
@login_required
def like_tweet(request, id):
    if request.method == 'POST':
        post = Post.objects.get(id=id)
        value = json.loads(request.body).get('value',0)
        print(request.POST)
        if value == 1:                         # value = 1 when the user retweets the post
            try:
                Like.objects.create(user=request.user, post=post)
                print("success")
            except IntegrityError:             # To prevent user from liking twice,
                print("integrity")
                value = 0                      # Like model has a unique constraint on (user,post) pairs
                
        elif value == -1:                      # value = 1 when the user retweets the post
            try:
                like = Like.objects.get(user=request.user, post=post).delete()
                print("success")
            except Like.DoesNotExist:    
                print("doesn't exist")
                value = 0
        return JsonResponse(data={'likes': value})

    return HttpResponseNotAllowed(['POST'])

@csrf_exempt
@login_required
def retweet(request, id):
    if request.method == 'POST':
        post = Post.objects.get(id=id)
        value = json.loads(request.body).get('value',0) 
        if value == 1:                          # value = 1 when the user likes the post
            try:
                Retweet.objects.create(user=request.user, post=post)
                print("retweeted")
            except IntegrityError:              # To prevent user from retweeting twice,
                value = 0                       # Retweet model has a unique constraint on (user,post) pairs
            else:                              
                bulk_insert_feed(post=post,
                                 activity_type="RT",
                                 actor=request.user,
                                 batch_size=100)        # Update Feed table for all of the user's followers

        elif value == -1:                       # value = -1 when the user un-likes the post
            try:
                like = Retweet.objects.get(user=request.user, post=post).delete()
            except Retweet.DoesNotExist:
                value = 0
            else:
                Feed.objects.filter(publisher=request.user).delete()
        return JsonResponse(data={'retweets': value})

    return HttpResponseNotAllowed(['POST'])

@login_required
def comment(request, username, id):
    try:
        parent_post = Post.objects.get(id=id)
    except Post.DoesNotExist:
        return missing_page(request, type_='Parent')
    
    if request.method == 'GET':
        request.session['success_url'] = request.META['HTTP_REFERER']
        return render(request, 'twitter/comment_form.html', 
                      context={
                          'parent_post': parent_post,
                          'replying_to_other': request.user != parent_post.author,
                          'placeholder': "Add another tweet" if request.user == parent_post.author 
                                                        else "Tweet your reply"
                          })

    elif request.method == 'POST':
        post = Post.objects.create(author=request.user, content=request.POST['content'], 
                                    post_type='C', parent_post=parent_post)
        bulk_insert_feed(post=post,
                         activity_type="CM",
                         actor=request.user,
                         batch_size=100)             # Update Feed table for all of the user's followers
        success_url = request.session.pop('success_url', reverse('home'))
        return HttpResponseRedirect(success_url)
    
    return HttpResponseNotAllowed(['GET', 'POST'])

@login_required    
def feed(request):
    request_user = request.user
    if request.method == 'GET':
        page_num = 1
        page_size = 20
        offset = (page_num / page_size) + 1
        posts = Feed.objects.filter(subscriber__id=request.user.id)   \
                            .order_by('-timestamp')[offset : offset+page_size]
        context = {
            'user': request_user,
            'posts': [{'obj'     : post,
                    'liked_by_me'  : True if Like.objects.filter(user__id=request_user.id, post__id=post.id).exists()
                                        else False,
                    'rtd_by_me'    : True if Retweet.objects.filter(user__id=request_user.id, post__id=post.id).exists()
                                        else False,
                    'like_count': post.likes.count(),
                    'rt_count'  : post.retweets.count(),
                    'cmt_count' : post.comments.count(),
                    'time_since': 0
                        } for post in posts],
        }
        return render(request, 'twitter/home.html', context)

    return HttpResponseNotAllowed(['GET'])
