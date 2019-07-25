from django.template.defaulttags import register
from django import template

register = template.Library()


@register.filter
def get(data, key):
    return data.get(key, '')
