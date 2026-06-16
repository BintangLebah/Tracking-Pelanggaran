from django import template
from django.urls import resolve, reverse, NoReverseMatch

register = template.Library()

@register.filter
def is_active(request, url_name):
    if not request:
        return False
    try:
        resolved = resolve(request.path_info)
        url_resolved = reverse(url_name)
        return resolved.url_name == url_name or request.path == url_resolved
    except (NoReverseMatch, Exception):
        return False