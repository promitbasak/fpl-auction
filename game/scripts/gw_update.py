import requests, json
from tqdm import tqdm

from django.db.models import Sum

from game.models import Manager, PlayerGameWeek, Player, ManagerGameWeek

field_map = {
    "total_points": "gw_points", 
    "value": "now_cost"
}

def run(*args):
    gw = int(args[0])
    update_managers = bool(int(args[1])) if len(args)>1 else True
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
        count = ManagerGameWeek.objects.filter(gw=gw).count()
        if count>0:
            raise Exception("Manager GW already exists!")
        for manager in tqdm(Manager.objects.all()):
            gw_points_agg = (manager.playergameweek_set.filter(gw=gw)
                                .aggregate(Sum("gw_points")).get("gw_points__sum"))
            gw_points = int(gw_points_agg) if gw_points_agg else 0
            total_bid_agg = (manager.playergameweek_set.filter(gw=gw)
                                .aggregate(Sum("current_bid")).get("current_bid__sum"))
            total_bid = round(total_bid_agg, 4) if total_bid_agg else 0.0
            mgw = ManagerGameWeek(gw=gw, gw_points=gw_points, total_bid=total_bid, manager=manager)
            mgw.save()
            manager.total_points = manager.total_points + gw_points
            manager.save()

            



