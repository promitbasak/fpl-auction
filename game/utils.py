from types import SimpleNamespace
import pytz

from .models import ( AuctionBid, 
                      Manager, 
                      Player, 
                      Parameters, 
                      TransferHistory, 
                      ManagerGameWeek, 
                      Deadlines, 
                      TransferOffer
)   
from .constants import (squad_rules,
                        min_benched_player,
                        player_buy_penalty,
                        player_sell_penalty,
                        player_offer_buy_penalty,
                        player_offer_sell_penalty,
                        player_sell_cost_decrease
)                        
from .validators import (
    offer_create_post_validator,
    squad_validation_mgw,
    offer_accept_validator,
    offer_delete_validator,
    team_validation
)
from django.utils import timezone


def dict_to_object(d):
    return SimpleNamespace(**d)


def get_current_gameweek():
    return Parameters.objects.filter().first().current_gameweek


def get_next_deadline(tz=None):
    time = Deadlines.objects.filter(finished=False, 
                        start_time__gte=timezone.now()).order_by("gw").first().start_time
    if time:
        time = time.astimezone(pytz.timezone("Asia/Dhaka")).strftime("%A, %d %B, %Y, %I:%M %p")
    return time
    

def commit_create_manager(user, name, team_name):
    manager = Manager(name=name, team_name=team_name, total_bid=0.0, user=user)
    manager.save()

    user.is_manager = True
    user.save()

    current_gameweek = Parameters.objects.all().first().current_gameweek
    for gw in range(1, current_gameweek+1):
        ManagerGameWeek.objects.create(gw=gw, manager=manager, total_bid=0, gw_points=0)


def commit_edit_manager(user, name, team_name):
    try:
        Manager.objects.filter(id=user.manager.id).update(name=name, team_name=team_name)
        virdict = True
        message = "Manager profile updated successfully"
    except Exception as e:
        virdict = False
        message = repr(e)
    return virdict, message


def add_random_benched_players_to_squad(mgw: ManagerGameWeek):
    added = 0
    if mgw.squad.all().count() < squad_rules["squad_size"]:
        for player in mgw.benched.all():
            is_valid, _ = squad_validation_mgw(mgw, in_player=player)
            if is_valid:
                mgw.benched.remove(player)
                mgw.squad.add(player)
                mgw.save()
                added += 1
    return added


def commit_player_buy(manager: Manager, player: Player, bid_value, offer=False, auction=False):
    current_gameweek = Parameters.objects.all().first().current_gameweek
    try:
        mgw = ManagerGameWeek.objects.get(gw=current_gameweek, manager=manager)
    except:
        return False
    player.bought_by = manager
    player.bought = True
    player.current_bid = bid_value
    player.save()

    manager.total_bid = round(manager.total_bid + bid_value, 4)
    manager.save()

    mgw.total_bid = round(mgw.total_bid + bid_value, 4)
    is_squad, _ = squad_validation_mgw(mgw, in_player=player)
    if is_squad:
        mgw.squad.add(player)
    else:
        mgw.benched.add(player)
    mgw.save()

    mgw = ManagerGameWeek.objects.get(gw=current_gameweek, manager=manager)
    added = add_random_benched_players_to_squad(mgw)

    if offer:
        manager.total_points = round(manager.total_points - player_offer_buy_penalty, 4)
        manager.point_penalties = round(manager.point_penalties + player_offer_buy_penalty, 4) 
        manager.save()
    else:
        trans_hist = TransferHistory(player=player, to_manager=manager, bid=bid_value, type=1)
        trans_hist.save()
        if not auction:
            manager.total_points = round(manager.total_points - player_buy_penalty, 4)
            manager.point_penalties = round(manager.point_penalties + player_buy_penalty, 4)
            manager.save()
    return True


def commit_player_sell(manager: Manager, player: Player, bid_value, offer=False, auction=False):
    current_gameweek = Parameters.objects.all().first().current_gameweek
    try:
        mgw = ManagerGameWeek.objects.get(gw=current_gameweek, manager=manager)
    except:
        return False

    player.bought_by = None
    player.bought = False
    player.current_bid = None
    player.base_bid = player.now_cost
    player.save()

    if not offer:
        bid_value = round(bid_value - player_sell_cost_decrease, 4)

    manager.total_bid = round(manager.total_bid - bid_value, 4)
    manager.save()

    mgw.total_bid = round(mgw.total_bid - bid_value, 4)
    mgw.squad.remove(player) if player in mgw.squad.all() else mgw.benched.remove(player)
    mgw.save()

    mgw = ManagerGameWeek.objects.get(gw=current_gameweek, manager=manager)
    added = add_random_benched_players_to_squad(mgw)


    if offer:
        manager.total_points = round(manager.total_points - player_offer_sell_penalty, 4)
        manager.point_penalties = round(manager.point_penalties + player_offer_sell_penalty, 4)
        manager.save()
    else:
        trans_hist = TransferHistory(player=player, from_manager=manager, bid=bid_value, type=2)
        trans_hist.save()
        if not auction:
            manager.total_points = round(manager.total_points - player_sell_penalty, 4)
            manager.point_penalties = round(manager.point_penalties + player_sell_penalty, 4)
            manager.save()
    return added


def commit_player_swap(manager: Manager, in_player, out_player):
    current_gameweek = Parameters.objects.all().first().current_gameweek
    try:
        mgw = ManagerGameWeek.objects.get(gw=current_gameweek, manager=manager)
    except:
        return False

    if in_player in mgw.benched.all() and out_player in mgw.squad.all():
        virdict, message = squad_validation_mgw(mgw, in_player=in_player, out_player=out_player)
        if virdict:
            mgw.benched.remove(in_player)
            mgw.squad.add(in_player)
            mgw.squad.remove(out_player)
            mgw.benched.add(out_player)
            mgw.save()
            message = "Player substituted successfully"
    else:
        virdict = False
        message = "Invalid player choice"
    
    return virdict, message


def commit_offer_create(manager: Manager, to_manager: Manager, player: Player, bid):
    virdict, message, bid_value = offer_create_post_validator(manager, to_manager, player, bid)
    if virdict:
        TransferOffer.objects.create(player=player, from_manager=manager, to_manager=to_manager, bid=bid_value)
    return virdict, message


def commit_offer_accept(manager: Manager, offer: TransferOffer):
    virdict, message = offer_accept_validator(manager, offer)
    if virdict:
        added = commit_player_sell(offer.to_manager, offer.player, offer.bid, offer=True)
        commit_player_buy(offer.from_manager, offer.player, offer.bid, offer=True)
        TransferHistory.objects.create(player=offer.player, from_manager=offer.to_manager,
                                        to_manager=offer.from_manager, bid=offer.bid, type=3)
        TransferOffer.objects.filter(pk=offer.id).delete()
    if message and message.startswith("You do not have sufficient balance."):
        message = "Offerer manager does not have sufficient balance."
    return virdict, message


def commit_offer_discard(manager: Manager, offer: TransferOffer):
    virdict, message = offer_delete_validator(manager, offer)
    if virdict:
        TransferOffer.objects.filter(pk=offer.id).delete()
        message = "Offer was discarded"
    return virdict, message


def get_all_squad_players(manager: Manager):
    current_gameweek = Parameters.objects.all().first().current_gameweek
    try:
        mgw = ManagerGameWeek.objects.get(gw=current_gameweek, manager=manager)
    except:
        return None
    goalkeepers = mgw.squad.all().filter(element_type__position="GKP")
    defenders = mgw.squad.all().filter(element_type__position="DEF")
    midfielders = mgw.squad.all().filter(element_type__position="MID")
    forwards = mgw.squad.all().filter(element_type__position="FWD")
    benched = mgw.benched.all()
    return {
                "goalkeepers": goalkeepers,
                "defenders": defenders,
                "midfielders": midfielders, 
                "forwards": forwards,
                "benched": benched,
                "squad": goalkeepers | defenders | midfielders | forwards,
            }


def squad_truncate(manager: Manager, gw=None):
    current_gameweek = Parameters.objects.all().first().current_gameweek if not gw else gw
    try:
        mgw = ManagerGameWeek.objects.get(gw=current_gameweek, manager=manager)
    except:
        return False
    if mgw.benched.all().count() < min_benched_player:
        num_count = min_benched_player - mgw.benched.all().count()
        players = mgw.squad.all().order_by("-current_bid", "-now_cost")[:num_count]
        for player in players:
            mgw.squad.remove(player)
            mgw.benched.add(player)
        mgw.save()



def add_warning_to_offers(queryset):
    warnings = []
    virdicts = []
    for offer in queryset:
        team_validation
        is_valid, warning_message = team_validation(offer.to_manager, out_player=offer.player)
        virdicts.append(is_valid)
        warnings.append(warning_message)
    return warnings, virdicts


def commit_auction_approve(auction_bid):
    success, msg = False, None
    manager = auction_bid.highest_bidder
    highest_bid = auction_bid.highest_bid
    player = auction_bid.player
    if manager and highest_bid:
        commit_player_buy(manager, player, highest_bid, auction=True)
        auction_bid.is_sold = True
        auction_bid.save()
        success = True
        msg = f"{manager.name} has bought {player.web_name} for " 
        msg += f"{highest_bid}."
    else:
        msg = f"{player.web_name} was not sold"
        AuctionBid.objects.filter(pk=auction_bid.id).delete()
    return success, msg


def commit_auction_bid(auction_bid, manager, bid_value):
    auction_bid.highest_bid = bid_value
    auction_bid.highest_bidder = manager
    auction_bid.save()


def get_auction_bid():
    auction_bids = AuctionBid.objects.filter(is_sold=False).order_by("-time")
    if len(auction_bids) < 1:
        return None
    elif len(auction_bids) > 1:
        for auction_bid in auction_bids[2:]:
            commit_auction_approve(auction_bid)
    return auction_bids.first()


def commit_auction_create(player):
    if AuctionBid.objects.filter(player=player).count():
        return False
    AuctionBid.objects.create(player=player, base_bid=player.base_bid, is_sold=False, highest_bid=0)
    return True