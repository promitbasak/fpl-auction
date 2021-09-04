import requests, json
from tqdm import tqdm

from game.models import PlayerType, PlayerStatus, Player, Team, Parameters, Deadlines, Manager

def run():
    status_map = {
        "n": "not_available",
        "d": "illness",
        "a": "active",
        "s": "suspended",
        "u": "not_in_league",
        "i": "injured"
    }

    if Player.objects.count() > 0:
        raise Exception("Player not empty")
    
    if Manager.objects.count() > 0:
        raise Exception("Manager not empty")

    confirm = input(f"Data will be initialized. Enter y to continue: ")
    if not confirm=="y":
        print("Operation aborted.")
        return None

    response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
    raw = json.loads(response.text)

    teams_raw = raw["teams"]
    players_raw = raw["elements"]
    types_raw = raw["element_types"]
    events_raw = raw["events"]


    # Create deadlines
    for event in events_raw:
        gw = event["id"]
        start_time = event["deadline_time"]
        Deadlines.objects.create(gw=gw, start_time=start_time)

    # Create types
    types = [(t["id"], t["singular_name_short"], t["singular_name"],
                t["squad_select"], t["squad_min_play"], t["squad_max_play"]) for t in types_raw]
    for (fpl_id,position,position_verbose,squad_select,squad_min_play,squad_max_play) in types:
        player_type = PlayerType.objects.create(fpl_id=fpl_id,position=position, position_verbose=position_verbose,
                                    squad_select=squad_select, squad_min_play=squad_min_play,
                                    squad_max_play=squad_max_play)
        player_type.save()


    # create teams
    teams = [(t["id"], t["code"], t["name"], t["short_name"]) for t in teams_raw]
    for (fpl_id, fpl_code, name, short_name) in teams:
        team = Team.objects.create(fpl_id=fpl_id,fpl_code=fpl_code, name=name,short_name=short_name)
        team.save()



    # create players
    fields = ["fpl_code", "fpl_id", "element_type", "first_name", "second_name", "web_name", "photo",
            "now_cost", "minutes", "team", "status", "total_points", "goals_scored", "assists", 
            "clean_sheets", "own_goals", "penalties_saved", "penalties_missed", "yellow_cards", 
            "red_cards", "saves", "bonus", "form", "selected_by_percent"]

    fpl_fields = ["code", "id", "element_type", "first_name", "second_name", "web_name", "photo",
                "now_cost", "minutes", "team", "status", "total_points", "goals_scored", "assists", 
                "clean_sheets", "own_goals", "penalties_saved", "penalties_missed", "yellow_cards", 
                "red_cards", "saves", "bonus", "form", "selected_by_percent"]

    cal_fields = ["base_cost", "base_bid"]

    for p in tqdm(players_raw):
        player_data = [p[fpl_field] for fpl_field in fpl_fields]
        player_dict = dict(zip(fields, player_data))
        player_dict["total_points"] = 0
        player_dict["team"] = Team.objects.get(fpl_id=player_dict["team"])
        player_dict["element_type"] = PlayerType.objects.get(fpl_id=player_dict["element_type"])
        player_dict["status"], _ = PlayerStatus.objects.get_or_create(status=player_dict["status"],
                                                        status_verbose=status_map[player_dict["status"]])
        player_dict["now_cost"] = player_dict["now_cost"]/10
        player_dict["base_cost"] = round(player_dict["now_cost"]*2)/2
        player_dict["base_bid"] = player_dict["base_cost"]-1
        player_dict["bought"] = False
        player = Player.objects.create(**player_dict)
        player.save()


    Parameters.objects.create(current_gameweek=1)