from django.contrib import auth
from django.http.request import HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, JsonResponse
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login as session_login, logout as session_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from .models import User, Post, Like, Retweet, Feed, Config
from .forms import SignupForm
from .utils import create_new_user, signup_info, update_signup_info, tweet_thread
from sawo import getContext, verifyToken
import json

config = Config.objects.order_by('-api_key')[:1]

def index(request):
    return render(request, 'twitter/index.html', {'title':'Join Twitter'})

def signup(request):
    if request.method == 'GET':
        context = {
            "title": 'Join Twitter',
            "form": SignupForm(initial=signup_info(request.session)),
        }
    elif request.method == 'POST': 
        form = SignupForm(request.POST)
        if form.is_valid():
            update_signup_info(request)
            return HttpResponseRedirect(reverse('login'))
        context = {'title': 'Join Twitter','form':form}
    return render(request, 'twitter/signup.html', context) 

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
    return HttpResponse(reverse('login'))

@login_required
def logout(request):
    session_logout(request)
    return HttpResponsePermanentRedirect(reverse('index'))

@login_required
def home(request):
    return render(request, 'twitter/home.html', {'title': "Home"})

@login_required
def tweet_detail(request, username, tweet_id):
    tweet = Post.objects.get(id=tweet_id)
    comments = Post.objects.filter(parent_post__id=tweet_id)[:]
    comments = [tweet_thread(comment) for comment in comments]
    context = {
        'tweet': tweet,
        'comments': comments,
    }
    render(request, 'twitter/tweet.html', context)

@login_required
def profile_tweets(request, username):
    offset = request.GET.get('offset', default=0)
    limit = request.GET.get('offset', default=19)

    top_tweets = Post.objects.filter(author__username=username)    \
                             .order_by('-timestamp')[offset:limit+1]
    context = {
        'bundles':[tweet_thread(tweet) for tweet in top_tweets]
    }

    return render(request, 'twitter/profile.html', context)


class TweetCreateView(LoginRequiredMixin, generic.CreateView):
    model = Post
    fields = ['content']
    template_name = 'twitter/home.html'


class FeedView(LoginRequiredMixin, generic.ListView):
    paginate_by = 20
    template_name = 'twitter/home.html'

    def get_queryset(self):
        return Feed.objects.filter(subscriber__email=self.request.user.email)   \
                           .order_by('-timestamp')
