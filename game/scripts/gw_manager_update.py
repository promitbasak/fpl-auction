from tqdm import tqdm

from django.db.models import Sum

from game.models import Manager, ManagerGameWeek

def run(*args):
    gw = int(args[0])
    count = ManagerGameWeek.objects.filter(gw=gw).count()
    if count>0:
        raise Exception("Manager GW already exists!")
    for manager in tqdm(Manager.objects.all()):
        gw_points = (manager.playergameweek_set.filter(gw=gw)
                            .aggregate(Sum("gw_points")).get("gw_points__sum"))
        print(manager.playergameweek_set.filter(gw=gw))
        print(manager.playergameweek_set.filter(gw=gw).aggregate(Sum("gw_points")))
        total_bid = (manager.playergameweek_set.filter(gw=gw)
                            .aggregate(Sum("current_bid")).get("current_bid__sum"))
        mgw = ManagerGameWeek(gw=gw, gw_points=gw_points, total_bid=total_bid, manager=manager)
        mgw.save()
        manager.total_points += gw_points
        manager.save()