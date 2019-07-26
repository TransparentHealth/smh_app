from django.template.defaulttags import register


@register.filter
def get(data, key):
    return data.get(key, '')
