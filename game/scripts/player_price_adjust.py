from game.models import Player
from django.db.models import Q

def run(*args):

    raise Exception("You are not supposed to run this script")
    assert False

    confirm = input(f"mgw will be copied. Enter y to continue: ")
    if not confirm=="y":
        print("Operation aborted.")
        return None

    for player in Player.objects.filter(~Q(bought=True)):
        player.base_bid = player.now_cost
        player.save()

