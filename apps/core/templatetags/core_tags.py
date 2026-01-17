"""
Core template tags and filters for the Ripple application.
"""
from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def percentage(value, max_value):
    """Calculate percentage of value against max_value"""
    try:
        if not max_value or float(max_value) == 0:
            return 0

        value = float(value)
        max_value = float(max_value)
        result = min(100, int((value / max_value) * 100))  # Cap at 100%
        return result
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def multiply(value, arg):
    """Multiply value by argument"""
    return float(value) * float(arg)


@register.filter
def divide(value, arg):
    """Divide value by argument"""
    if float(arg) == 0:
        return 0
    return float(value) / float(arg)


@register.filter(name='split')
def split(value, arg):
    """Split the value by the argument and return the list"""
    if value is None:
        return []
    return value.split(arg)


@register.filter
def sum_attr(queryset, attr_name):
    """Sum a specific attribute across all objects in a queryset"""
    total = 0
    for obj in queryset:
        value = getattr(obj, attr_name, 0)
        if value:
            total += float(value)
    return total


@register.filter
def filter_by(queryset, filter_string):
    """Filter a queryset by attribute=value"""
    if not filter_string or ',' not in filter_string:
        return queryset

    attr, value = filter_string.split(',', 1)
    kwargs = {attr: value}
    return [obj for obj in queryset if str(getattr(obj, attr, None)) == value]
