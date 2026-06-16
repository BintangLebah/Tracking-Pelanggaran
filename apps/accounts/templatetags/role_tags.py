from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def active_if_current(context, ns, name, class_name='menu-active'):
    """
    Template tag untuk menambahkan class active berdasarkan URL saat ini.

    Usage:
        {% active_if_current 'dashboards' 'guru' %}
    """
    request = context.get('request')
    if not request:
        return ''

    resolved_ns = getattr(request.resolver_match, 'namespace', None),
    resolved_name = getattr(request.resolver_match, 'url_name', None),

    # Compare both namespace and url_name
    if ns == resolved_ns and name == resolved_name:
        return class_name
    return ''