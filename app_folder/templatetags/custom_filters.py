from django import template

register = template.Library()

@register.filter
def truncate_title(value, length=20):
    if len(value) > length:
        return value[:length] + '...'
    return value
