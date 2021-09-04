from tqdm import tqdm

from django.db.models import Sum

from game.models import Deadlines, Manager, ManagerGameWeek, Parameters
from game.utils import squad_truncate

def run(*args):

    raise Exception("You are not supposed to run this script")
    assert False

    confirm = input(f"mgw will be copied. Enter y to continue: ")
    if not confirm=="y":
        print("Operation aborted.")
        return None

    gw = int(args[0])
    for manager in tqdm(Manager.objects.all()):
        mgw = ManagerGameWeek.objects.get(gw=gw, manager=manager)
        squad_truncate(manager, gw=gw)
        gw_points = 0
        for player in mgw.squad.all():
            try:
                gw_points += player.playergameweek_set.get(gw=gw).gw_points
            except:
                pass
        total_bid_agg = (manager.playergameweek_set.filter(gw=gw)
                            .aggregate(Sum("current_bid")).get("current_bid__sum"))
        total_bid = round(total_bid_agg, 4) if total_bid_agg else 0.0
        
        manager.total_points = manager.total_points + gw_points
        manager.save()
        mgw = ManagerGameWeek.objects.get(gw=gw, manager=manager)
        mgw.gw_points = gw_points
        mgw.total_bid = total_bid
        mgw.save()

        # create a copy of mgw
        current_gw = gw + 1
        new_mgw, created = ManagerGameWeek.objects.get_or_create(gw=current_gw, manager=manager)
        if not created:
            new_mgw.squad.all().delete()
            new_mgw.benched.all().delete()
        new_mgw.squad.add(*mgw.squad.all())
        new_mgw.benched.add(*mgw.benched.all())
        new_mgw.total_bid = mgw.total_bid
        new_mgw.total_points = 0.0
        new_mgw.save()

    # set the deadline finished
    Deadlines.objects.filter(gw__lt=current_gw).update(finished=True)

    # increment the current game week
    parameter = Parameters.objects.all().first()
    parameter.current_gameweek = parameter.current_gameweek + 1
    parameter.save()