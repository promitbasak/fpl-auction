from game.utils import squad_truncate
import requests, json
from tqdm import tqdm
from django.utils import timezone

from django.db.models import Sum

from game.models import Manager, PlayerGameWeek, Player, ManagerGameWeek, Parameters, Deadlines
from game.utils import get_current_gameweek


field_map = {
    "total_points": "gw_points", 
    "value": "now_cost"
}


def is_gameweek_valid(gw):
    print("validating the gameweek ...")
    messages = []
    start_time = Deadlines.objects.get(gw=gw).start_time
    print("getting data from fpl api ...")
    resp = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
    raw = json.loads(resp.text)
    is_finished = raw["events"][gw-1]["finished"]
    if not is_finished:
        messages.append("GW not finished according to fpl api")
    if (timezone.now()-start_time).days < 3:
        messages.append("GW should start at least 3 days before")
    if gw != 1 and PlayerGameWeek.objects.filter(gw=gw-1).count() < 1:
        messages.append("Previous player gw data not found")
    if ManagerGameWeek.objects.filter(gw=gw).count() < 1:
        messages.append("Current manager gw data not found")
    if PlayerGameWeek.objects.filter(gw=gw).count() > 0:
        messages.append("Current gw player data found")
    if ManagerGameWeek.objects.filter(gw=gw+1).count() > 0:
        messages.append("Next gw manager data found")
    if Parameters.objects.count() > 1:
        messages.append("More than one parameters found")
    
    is_valid = False if len(messages)>0 else True
    return is_valid, messages


def run(*args):
    gw = int(args[0])
    update_managers = bool(int(args[1])) if len(args)>1 else True


    is_valid, messages = is_gameweek_valid(gw)
    if not is_valid:
        print(f"Gameweek: {gw} cannot be validated. Warning messages are: ")
        print(messages)
        print("Operation aborted.")
        return None


    confirm = input(f"Gameweek: {gw} will be updated. Enter y to continue: ")
    if not confirm=="y":
        print("Operation aborted.")
        return None
    
    confirm = input(f"Please dump the database now. Enter yes after you dumped it: ")
    if not confirm=="yes":
        print("Operation aborted.")
        return None


    count = PlayerGameWeek.objects.filter(gw=gw).count()
    if count>0:
        raise Exception("Player GW already exists!")
    base_url = "https://fantasy.premierleague.com/api/element-summary/{}/"
    for player_id in tqdm(Player.objects.all().values_list("fpl_id", flat=True)):
        url = base_url.format(player_id)
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Invalid response code: {response.status_code}")
        player_data = json.loads(response.text)
        history = player_data["history"]
        gw_data = [data for data in history if data["round"]==gw]
        fpl_fields = ["minutes", "total_points", "goals_scored", "assists", 
                "clean_sheets", "own_goals", "penalties_saved", "penalties_missed", "yellow_cards", 
                "red_cards", "saves", "bonus", "value"]
        gw_dict = dict(zip(fpl_fields, [0]*len(fpl_fields)))
        if len(gw_data)!=0:
            for data in gw_data:
                for k,v in gw_dict.items():
                    gw_dict[k] = gw_dict[k] + data[k]
            gw_dict["value"] = data["value"]
        for k,v in field_map.items():
            gw_dict[v] = gw_dict[k]
            del gw_dict[k]
        gw_dict["now_cost"] /= 10
        gw_dict["now_cost"] = round(gw_dict["now_cost"], 4)
        player = Player.objects.get(fpl_id=player_id)
        gw_dict["gw"], gw_dict["current_bid"] = gw, player.current_bid
        gw_dict["bought_by"], gw_dict["player"] = player.bought_by, player
        pgw = PlayerGameWeek(**gw_dict)
        pgw.save()

    if update_managers:
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