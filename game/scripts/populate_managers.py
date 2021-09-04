from tqdm import tqdm

from django.contrib.auth import get_user_model

from game.models import Manager, Player, Deadlines
from game.utils import commit_player_buy, commit_create_manager
from game.validators import player_buy_post_validation


def run():

    raise Exception("You are not supposed to run this script")
    assert False

    confirm = input(f"mgw will be copied. Enter y to continue: ")
    if not confirm=="y":
        print("Operation aborted.")
        return None

    User = get_user_model()

    for username, password, email, name, team_name in (
            ("promitbasak", "ashphalt", "basakpromit@gmail.com", "Promit", "Omega"),
            ("babulhayat", "ashphalt", "ab@hg.sjd", "Babul Hayat", "Babul"),
            ("user1", "ashphalt", "ag@hg.sjd", "Sheldon", "Always Blue"),
        ):
        user = User.objects.create_user(username=username, password=password, email=email)
        commit_create_manager(user, name, team_name)

    Deadlines.objects.filter(gw__lte=3).update(finished=True)

    for pos,count in tqdm([("GKP", 2), ("DEF", 5), ("MID", 5), ("FWD", 3)]):
        i = 0
        for manager in Manager.objects.all():
            players = Player.objects.filter(element_type__position=pos).order_by("-total_points", "fpl_id")[i:i+count]
            for player in players:
                bid_value = player.base_bid
                success, msg, _ = player_buy_post_validation(manager, player, bid_value)
                print(f"{manager.name}: {msg}")
                if success:
                    commit_player_buy(manager, player, bid_value)
            i += count

    for username, password, email, name, team_name in (
            ("demo", "ashphalt", "fsf@dgd.cofdm", "Demo", "Demo"),
        ):
        user = User.objects.create_user(username=username, password=password, email=email)
        commit_create_manager(user, name, team_name)
    
    for username, password, email, name, team_name in (
            ("demo2", "ashphalt", "ffsf@dgd.cofdm", "Demo2", "Demo2"),
        ):
        user = User.objects.create_user(username=username, password=password, email=email, is_manager=False)
        user.save()