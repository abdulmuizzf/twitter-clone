from django.urls import path

from . import views

#app_name = ''

urlpatterns = [
    path('', views.FeedView.as_view(), name='home'),
    path('home/', views.home, name='home'),
    path('index/', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('<username>/tweets/', views.profile_tweets, name='profile-tweets'),
    path('compose/tweet/', views.TweetCreateView.as_view(), name='create-tweet'),
    path('<username>/status/<int:id>/', views.tweet_detail, name='tweet-detail'),
]