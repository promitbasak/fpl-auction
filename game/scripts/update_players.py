import requests, json
from tqdm import tqdm

from game.models import PlayerType, PlayerStatus, Player, Team, Parameters, PlayerGameWeek

def run():
    status_map = {
        "n": "not_available",
        "d": "illness",
        "a": "active",
        "s": "suspended",
        "u": "not_in_league",
        "i": "injured"
    }

    confirm = input(f"Are you sure to update players? Enter y to continue: ")
    if not confirm=="y":
        print("Operation aborted.")
        return None

    response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
    raw = json.loads(response.text)

    players_raw = raw["elements"]

    current_gameweek = Parameters.objects.all().first().current_gameweek

    print("current_gameweek:", current_gameweek)


    # create players
    fields = ["fpl_code", "fpl_id", "element_type", "first_name", "second_name", "web_name", "photo",
            "now_cost", "minutes", "team", "status", "goals_scored", "assists", 
            "clean_sheets", "own_goals", "penalties_saved", "penalties_missed", "yellow_cards", 
            "red_cards", "saves", "bonus", "form", "selected_by_percent"]

    fpl_fields = ["code", "id", "element_type", "first_name", "second_name", "web_name", "photo",
                "now_cost", "minutes", "team", "status", "goals_scored", "assists", 
                "clean_sheets", "own_goals", "penalties_saved", "penalties_missed", "yellow_cards", 
                "red_cards", "saves", "bonus", "form", "selected_by_percent"]

    players_added = 0
    print("current_gameweek:", current_gameweek)
    for p in tqdm(players_raw):
        player_data = [p[fpl_field] for fpl_field in fpl_fields]
        player_dict = dict(zip(fields, player_data))
        player_dict["team"] = Team.objects.get(fpl_id=player_dict["team"])
        player_dict["element_type"] = PlayerType.objects.get(fpl_id=player_dict["element_type"])
        player_dict["status"], _ = PlayerStatus.objects.get_or_create(status=player_dict["status"],
                                                        status_verbose=status_map[player_dict["status"]])
        player_dict["now_cost"] = player_dict["now_cost"]/10
        player_counts = Player.objects.filter(fpl_id=player_dict["fpl_id"]).count()
        player_dict["base_bid"] = player_dict["now_cost"]
        if player_counts:
            Player.objects.filter(fpl_id=player_dict["fpl_id"]).update(**player_dict)
        else:
            player_dict["total_points"] = 0
            player_dict["base_cost"] = round(player_dict["now_cost"]*2)/2
            player_dict["bought"] = False
            player = Player.objects.create(**player_dict)
            player.save()
            for gw in range(1, current_gameweek):
                PlayerGameWeek.objects.create(gw=gw, player=player)
            players_added += 1

    print(f"Total {players_added} players added.")
    print("current_gameweek:", current_gameweek)

