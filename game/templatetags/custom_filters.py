from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def manager_transfers(manager):
    return manager.to_transfer.all().union(manager.from_transfer.all())


@register.filter
def subtract(value, arg):
    return value - arg