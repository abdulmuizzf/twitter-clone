from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def msu(value):
    """ Reduce timesince value to its most significant unit"""
    num, unit = value.split(',')[0].split()
    return num+unit[0]

msu.is_safe = True
