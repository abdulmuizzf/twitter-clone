from django.core.files import File

from .models import User, Post

def create_new_user(request, email):
    print(
        {
            'email' : email,
            'username' : request.session['username'],
            'first_name' : request.session['display_name'],
            'bio': request.session['bio'],
        }
    )
    return User.objects.create_user(
        **{
            'email' : email,
            'username' : request.session.pop('username'),
            'first_name' : request.session.pop('display_name'),
            'bio': request.session.pop('bio'),
        }
    )

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

def tweet_thread(post):
    table = Post.objects.model._meta.db_table
    query = (
        "WITH RECURSIVE comment (id) AS ("
       f"   SELECT {table}.id FROM {table} WHERE id = {post.id}"
        "   UNION"
       f"   SELECT TOP 1 comment.id FROM comment, {table}"
       f"   WHERE comment.parent_post.id = {table}.id"
        ")"
        " SELECT * from comment"
    )
    return Post.objects.raw(query)
