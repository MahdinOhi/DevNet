from django import template

register = template.Library()

@register.filter
def split(value, delimiter=','):
    """
    Split a string by delimiter and return a list.
    Usage: {{ value|split:"," }}
    """
    if not value:
        return []
    return [item.strip() for item in str(value).split(delimiter) if item.strip()]

@register.filter
def strip(value):
    """
    Strip whitespace from the beginning and end of a string.
    Usage: {{ value|strip }}
    """
    if not value:
        return ''
    return str(value).strip()
