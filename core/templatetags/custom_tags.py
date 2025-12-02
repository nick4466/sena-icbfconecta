from django import template

register = template.Library()

@register.filter
def times(number):
    return range(int(number))

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
