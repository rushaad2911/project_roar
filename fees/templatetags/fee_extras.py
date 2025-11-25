from django import template
from django.db.models import Sum

register = template.Library()

@register.filter
def sum(queryset, property_name):
    """
    Template filter to sum a property across all objects in a queryset.
    Usage: {{ queryset|sum:'property_name' }}
    """
    if not queryset:
        return 0

    if hasattr(queryset[0], property_name):
        # If it's a regular property
        return sum(getattr(obj, property_name) or 0 for obj in queryset)
    elif hasattr(queryset[0], 'aggregate'):
        # If it's a queryset that can be aggregated
        return queryset.aggregate(Sum(property_name))[f'{property_name}__sum'] or 0

    return 0

@register.filter
def div(value, arg):
    """
    Template filter to divide a value by another.
    Usage: {{ value|div:arg }}
    """
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    """
    Template filter to multiply a value by another.
    Usage: {{ value|mul:arg }}
    """
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0

@register.filter
def sub(value, arg):
    """
    Template filter to subtract a value from another.
    Usage: {{ value|sub:arg }}
    """
    try:
        return float(value) - float(arg)
    except ValueError:
        return 0
