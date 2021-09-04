from .gw_update import run as gw_update_run
from .gw_update import field_map
from .update_players import run as update_players_run

from game.models import Parameters, Deadlines, PlayerGameWeek, ManagerGameWeek
from game.utils import get_current_gameweek
from .gw_update import is_gameweek_valid


field_map = {
    "total_points": "gw_points", 
    "value": "now_cost"
}   


def run(*args):
    try:
        gw = int(args[0])
    except:
        gw = Parameters.objects.all().first().current_gameweek
    
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

    print("Updating gameweek, do not close...")
    print("get_current_gameweek:", get_current_gameweek())
    args = gw, True
    gw_update_run(*args)

    print("get_current_gameweek:", get_current_gameweek())
    print("updating players, do not close ...")
    update_players_run()
    print("get_current_gameweek:", get_current_gameweek())
    print("Update completed :D")
