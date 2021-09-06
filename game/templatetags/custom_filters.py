from django import template
from django.db.models import Sum

from game.validators import check_incoming_offers, check_unstable_squad, check_auction_finished

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def manager_transfers(manager):
    return manager.to_transfer.all().union(manager.from_transfer.all()).order_by("-time")


@register.filter
def subtract(value, arg):
    return value - arg


@register.filter
def is_auction_finished(value):
    return check_auction_finished()


@register.filter
def team_value(manager):
    return round(manager.player_set.all().aggregate(Sum("current_bid")).get("current_bid__sum"), 4)

    

@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    """
    Return encoded URL parameters that are the same as the current
    request's parameters, only with the specified GET parameters added or changed.

    It also removes any empty parameters to keep things neat,
    so you can remove a parm by setting it to ``""``.

    For example, if you're on the page ``/things/?with_frosting=true&page=5``,
    then

    <a href="/things/?{% param_replace page=3 %}">Page 3</a>

    would expand to

    <a href="/things/?with_frosting=true&page=3">Page 3</a>

    Based on
    https://stackoverflow.com/questions/22734695/next-and-before-links-for-a-django-paginated-query/22735278#22735278
    """
    d = context['request'].GET.copy()
    for k, v in kwargs.items():
        d[k] = v
    for k in [k for k, v in d.items() if not v]:
        del d[k]
    return d.urlencode()


@register.simple_tag(takes_context=True)
def param_delete(context, param):
    """
    Return encoded URL parameters that are the same as the current
    request's parameters, only with the specified GET parameters added or changed.

    It also removes any empty parameters to keep things neat,
    so you can remove a parm by setting it to ``""``.

    For example, if you're on the page ``/things/?with_frosting=true&page=5``,
    then

    <a href="/things/?{% param_replace page=3 %}">Page 3</a>

    would expand to

    <a href="/things/?with_frosting=true&page=3">Page 3</a>

    Based on
    https://stackoverflow.com/questions/22734695/next-and-before-links-for-a-django-paginated-query/22735278#22735278
    """
    d = context['request'].GET.copy()
    if param in d:
        del d[param]
    return d.urlencode()

@register.simple_tag(takes_context=True)
def player_from_gameweek(context, **kwargs):
    gw = int(kwargs.get("gw"))
    player = kwargs.get("player")
    try:
        return player.playergameweek_set.get(gw=gw).gw_points 
    except:
        return None


# @register.simple_tag(takes_context=True)
# def is_unstable_squad(context, param):
#     virdict = check_unstable_squad(context['request'].user.manager)[0]
#     return virdict  

# @register.simple_tag(takes_context=True)
# def is_incoming_offers(context, param):
#     virdict = check_incoming_offers(context['request'].user.manager)[0]
#     return virdict 