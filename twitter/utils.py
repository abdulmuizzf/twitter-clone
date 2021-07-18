from django.core.files import File
from django.shortcuts import render
from itertools import islice

from .models import User, Post, Feed, Like, Retweet

def create_new_user(request, email):
    user = User.objects.create_user(
        **{
            'email' : email,
            'username' : request.session.pop('username'),
            'first_name' : request.session.pop('display_name'),
            'bio': request.session.pop('bio'),
        }
    )
    user.followers.add(user)
    return user

def bulk_insert_feed(post, activity_type, actor, batch_size):
    feed_list = ((follower,activity_type, post, actor, post.timestamp) for follower in actor.followers.all())
    while True:                    # Bulk INSERT in groups of <batch_size>
        batch = list(islice(feed_list, batch_size))
        if not batch:
            break
        Feed.objects.bulk_create(batch, batch_size)

def get_default_profile_pic():  
    return 

def signup_info(session):
    return {
            "display_name": session.get('display_name',''),
            "username": session.get('username',''),
            "bio": session.get('bio',''),
        }

def update_signup_info(request):
    request.session['display_name'] = request.POST['display_name']
    request.session['username'] = request.POST['username']
    request.session['bio'] = request.POST['bio']

def delete_signup_info(session):
    try:
        del session['display_name']
        del session['username']
        del session['bio']
    except KeyError:
        return



def tweet_thread(post, user):
    table = Post.objects.model._meta.db_table
    query = (
        "WITH RECURSIVE ct(id, parent_post_id, first_child, depth) AS ("
        f"   SELECT c.id, c.parent_post_id, c.first_child, 0 AS depth FROM {table} c WHERE c.id = {post.id}"
        "   UNION ALL"
        f"   SELECT ct.id, ct.parent_post_id, ct.first_child, (depth + 1) AS death FROM ct JOIN {table} c"
        f"   ON ct.parent_post_id = c.id WHERE ct.first_child = TRUE AND ct.depth < 3"
        ")"
        " SELECT * FROM ct"
    )
    thread = Post.objects.raw(query)
    return [{
        'obj': comment,
        'liked_by_me'  : True if Like.objects.filter(user__id=user.id, post__id=comment.id).exists()
                                else False,
        'rtd_by_me'    : True if Retweet.objects.filter(user__id=user.id, post__id=comment.id).exists()
                            else False,
        'like_count': comment.likes.count(),
        'rt_count'  : comment.retweets.count(),
        'cmt_count' : comment.comments.count(),
        'timesince' : 0
        } for comment in thread]

def missing_page(request, type_="Tweet"):
    if type_ == "Tweet" or type_ == "User":
        title = type_
        display_text = "Hmm... this page doesn't exist."
    elif type_ == "Parent":
        title = "Tweet"
        display_text = "This tweet was deleted."

    return render(request, 
                      template_name='twitter/_doesnotexist.html', 
                      context={'title': title,
                               'display_text': display_text})
