import requests, json
from tqdm import tqdm

from game.models import Manager, ManagerGameWeek, Parameters
from game.validators import squad_validation_mgw

def run(*args):

    raise Exception("You are not supposed to run this script")
    assert False

    confirm = input(f"mgw will be copied. Enter y to continue: ")
    if not confirm=="y":
        print("Operation aborted.")
        return None
    try:
        include_current_players = bool(int(args[0])) if args[0] else False
    except:
        include_current_players = False

    for manager in tqdm(Manager.objects.all()):
        current_gameweek = Parameters.objects.all().first().current_gameweek
        for gw in range(1, current_gameweek):
            try:
                mgw =  ManagerGameWeek.objects.get(gw=gw)
                if include_current_players:
                    total_bid, gw_points = 0, 0
                    for player in manager.player_set.all():
                        if squad_validation_mgw(mgw, in_player=player)[0]:
                            mgw.squad.add(player)
                            try:
                                gw_points += player.playergameweek_set.get(gw=1).gw_points
                            except:
                                pass
                        else:
                            mgw.benched.add(player)
                        total_bid += player.current_bid
                    mgw.total_bid = total_bid
                    mgw.gw_points = gw_points
                    mgw.save()
            except ManagerGameWeek.DoesNotExist:
                ManagerGameWeek.objects.create(gw=gw, manager=manager, total_bid=0, gw_points=0)
            except Exception as e:
                print(repr(e))
        # current gameweek
        try:
            mgw =  ManagerGameWeek.objects.get(gw=current_gameweek)
            if include_current_players: 
                total_bid, gw_points = 0, 0
                for player in manager.player_set.all():
                    if squad_validation_mgw(mgw, in_player=player)[0]:
                        mgw.squad.add(player)
                        try:
                            gw_points += player.playergameweek_set.get(gw=1).gw_points
                        except:
                            pass
                    else:
                        mgw.benched.add(player)
                    total_bid += player.current_bid
                mgw.total_bid = total_bid
                mgw.gw_points = gw_points
                mgw.save()
        except ManagerGameWeek.DoesNotExist as e:
            mgw = ManagerGameWeek.objects.create(gw=current_gameweek, manager=manager,
                                            total_bid=manager.total_bid, gw_points=0)
        except Exception as e:
            print(repr(e))

    
