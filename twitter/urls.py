from django.urls import path

from . import views

#app_name = ''

urlpatterns = [
    path('', views.feed),
    path('home/', views.feed, name='home'),
    path('index/', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('<username>/', views.profile_tweets, name='profile'),
    path('<username>/tweets/', views.profile_tweets, name='profile-tweets'),
    path('<username>/likes/', views.profile_likes, name='profile-likes'),
    path('compose/tweet/', views.create_tweet, name='create-tweet'),
    path('<username>/tweets/<int:id>/', views.tweet_detail, name='tweet-detail'),
    path('follow/<int:id>/', views.follow, name='follow'),
    path('like_tweet/<int:id>/', views.like_tweet, name='like'),
    path('retweet/<int:id>/', views.retweet, name='retweet'),
    path('<username>/tweets/<int:id>/comment/', views.comment, name='comment'),
    path('<username>/tweets/<int:id>/delete/', views.delete_tweet, name='delete-tweet'),
]


"""
post.obj.timestamp|timesince|truncatewords:2
"""