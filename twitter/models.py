from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .validators import UsernameValidator


class User(AbstractUser):
    username = models.CharField(
        _('username'),
        max_length=50,
        unique=True,
        help_text=_('Required. 50 characters or fewer. Letters, digits and _ only allowed.'),
        validators=[UsernameValidator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    password = None
    bio = models.CharField(max_length=160)
    profile_pic = models.ImageField(upload_to='profiles', blank=True, null=True)
    followers = models.ManyToManyField('User', related_name="following")


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.CharField(max_length=280)
    timestamp = models.DateTimeField(default=timezone.now)
    post_type = models.CharField(max_length=10, choices=[("O","Original"),("C","Comment")], default="O")
    parent_post = models.ForeignKey('Post', null=True, on_delete=models.CASCADE, related_name="comment")


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    class Meta:
        unique_together = ('user', 'post',)


class Retweet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    class Meta:
        unique_together = ('user', 'post',)


class Feed(models.Model):
    """
    Stores feed for every follower(subscriber) based on tweet, retweet & comment activity
    of followed users(publishers)
    """
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name="feed")
    activity_type = models.CharField(max_length=2, choices=[("TW","Tweet"),("RT","Retweet"),("CM","Comment")])
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    publisher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activity")


class Config(models.Model):
    api_key = models.CharField(max_length=200)
    identifier = models.CharField(max_length=200, choices = [("email","Email"),("phone_number_sms","Phone")])
