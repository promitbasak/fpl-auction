from django.utils import timezone
from django.urls import reverse_lazy

from .models import Deadlines, Manager, ManagerGameWeek, Player, Parameters, PlayerType, TransferOffer
from .constants import squad_rules, manager_max_balance, min_benched_player


pos_trans = {
    "FWD": "forward",
    "DEF": "defender",
    "MID": "midfielder",
    "GKP": "goalkeeper"
}


def check_deadline():
    """
    return True if the deadline is passed, player transactions wil not be possible then.
    """
    deadline_obj = Deadlines.objects.filter(finished=False).order_by("start_time").first()
    if deadline_obj:
        deadline = deadline_obj.start_time
        now_time = timezone.now()
        return now_time > deadline
    return False


def balance_validation(manager: Manager, bid_value):
    current_gameweek = Parameters.objects.all().first().current_gameweek
    try:
        mgw = ManagerGameWeek.objects.get(gw=current_gameweek, manager=manager)
    except:
        return False
    if mgw.total_bid + bid_value > manager_max_balance:
        return False
    return True


def get_reserved_player_counts(manager: Manager, exclude=None):
    current_gameweek = Parameters.objects.all().first().current_gameweek
    mgw = ManagerGameWeek.objects.get(gw=current_gameweek, manager=manager)
    counts = 0
    for position in PlayerType.objects.all().values_list("position", flat=True):
        if position==exclude:
            continue
        counts += max(squad_rules[f"{position}_min"] - mgw.squad.filter(element_type__position=position).count(), 0)
    return counts


def get_reserved_player_counts_mgw(mgw: ManagerGameWeek, exclude=None):
    counts = 0
    for position in PlayerType.objects.all().values_list("position", flat=True):
        if position==exclude:
            continue
        counts += max(squad_rules[f"{position}_min"] - mgw.squad.filter(element_type__position=position).count(), 0)
    return counts
    

def squad_validation(manager: Manager, in_player=None, out_player=None):
    in_pos = in_player.element_type.position if in_player else None
    out_pos = out_player.element_type.position if out_player else None
    current_gameweek = Parameters.objects.all().first().current_gameweek
    try:
        mgw = ManagerGameWeek.objects.get(gw=current_gameweek, manager=manager)
    except:
        return False, "Invalid gameweek"
    if in_player:
        protected = get_reserved_player_counts(manager, exclude=in_player.element_type.position)
    else:
        protected = get_reserved_player_counts(manager)
    message = None
    virdict = True
    if in_pos==out_pos:
        pass
    elif not out_pos and mgw.squad.all().count() + 1 > squad_rules["squad_size"] - protected:
        virdict = False
        message = "You need to keep room for other positions"
    elif not in_pos and mgw.squad.all().count() - 1 > squad_rules["squad_size"]:
        virdict = False
        message = "Maximum squad size exceeded"
    elif (in_pos and 
          mgw.squad.filter(element_type__position=in_pos).count()+1 > squad_rules[f"{in_pos}_max"]):
        message = f"Max num. of {pos_trans[in_pos]}s excedded: {squad_rules[f'{in_pos}_max']}"
        virdict= False
    elif (out_pos and 
          mgw.squad.filter(element_type__position=out_pos).count()-1 < squad_rules[f"{out_pos}_min"]):
        message = f"You will have less than minimum {squad_rules[f'{out_pos}_min']} {pos_trans[out_pos]}s"
        virdict= False
    return virdict, message


def squad_validation_mgw(mgw: ManagerGameWeek, in_player=None, out_player=None):
    in_pos = in_player.element_type.position if in_player else None
    out_pos = out_player.element_type.position if out_player else None
    if in_player:
        protected = get_reserved_player_counts_mgw(mgw, exclude=in_player.element_type.position)
    else:
        protected = get_reserved_player_counts_mgw(mgw)
    message = None
    virdict = True
    if in_pos==out_pos:
        pass
    elif not out_pos and mgw.squad.all().count() + 1 > squad_rules["squad_size"] - protected:
        virdict = False
        message = "You need to keep room for other positions"
    elif not in_pos and mgw.squad.all().count() - 1 > squad_rules["squad_size"]:
        virdict = False
        message = "Maximum squad size exceeded"
    elif (in_pos and 
          mgw.squad.filter(element_type__position=in_pos).count()+1 > squad_rules[f"{in_pos}_max"]):
        message = f"Max num. of {pos_trans[in_pos]}s excedded: {squad_rules[f'{in_pos}_max']}"
        virdict= False
    elif (out_pos and 
          mgw.squad.filter(element_type__position=out_pos).count()-1 < squad_rules[f"{out_pos}_min"]):
        message = f"You will have less than minimum {squad_rules[f'{out_pos}_min']} {pos_trans[out_pos]}s"
        virdict= False
    return virdict, message

def team_validation(manager: Manager, in_player=None, out_player=None):
    in_pos = in_player.element_type.position if in_player else None
    out_pos = out_player.element_type.position if out_player else None
    current_gameweek = Parameters.objects.all().first().current_gameweek
    try:
        mgw = ManagerGameWeek.objects.get(gw=current_gameweek, manager=manager)
    except:
        return False, "Invalid gameweek"
    message = None
    virdict = True
    if in_pos==out_pos:
        pass
    elif (in_pos and 
          mgw.squad.filter(element_type__position=in_pos).count() + 
          mgw.benched.filter(element_type__position=in_pos).count() + 1 > squad_rules[f"{in_pos}_max"]):
        message = f"Max num. of {pos_trans[in_pos]}s exceeded: {squad_rules[f'{in_pos}_max']}"
        virdict= False
    elif (out_pos and 
          mgw.squad.filter(element_type__position=out_pos).count() +
          mgw.benched.filter(element_type__position=out_pos).count() -1 < squad_rules[f"{out_pos}_min"]):
        message = f"You will have less than minimum {squad_rules[f'{out_pos}_min']} {pos_trans[out_pos]}s"
        virdict= False
    return virdict, message


def team_validation_mgw(mgw: ManagerGameWeek, in_player=None, out_player=None):
    in_pos = in_player.element_type.position if in_player else None
    out_pos = out_player.element_type.position if out_player else None
    message = None
    virdict = True
    if in_pos==out_pos:
        pass
    elif (in_pos and 
          mgw.squad.filter(element_type__position=in_pos).count() + 
          mgw.benched.filter(element_type__position=in_pos).count() + 1 > squad_rules[f"{in_pos}_max"]):
        message = f"Max num. of {pos_trans[in_pos]}s exceeded: {squad_rules[f'{in_pos}_max']}"
        virdict= False
    elif (out_pos and 
          mgw.squad.filter(element_type__position=out_pos).count() +
          mgw.benched.filter(element_type__position=out_pos).count() -1 < squad_rules[f"{out_pos}_min"]):
        message = f"You will have less than minimum {squad_rules[f'{out_pos}_min']} {pos_trans[out_pos]}s"
        virdict= False
    return virdict, message


def check_unstable_squad(manager: Manager):
    current_gameweek = Parameters.objects.all().first().current_gameweek
    try:
        mgw = ManagerGameWeek.objects.get(gw=current_gameweek, manager=manager)
    except:
        return False, "Invalid gameweek"
    message = None
    virdict = False
    if not manager:
        message = "You do not have manager profile"
        virdict = False
    elif mgw.squad.all().count() < squad_rules["squad_size"]:
        message = "Squad size is less than 11"
        virdict = True
    return virdict, message


def check_unstable_team(manager: Manager):
    current_gameweek = Parameters.objects.all().first().current_gameweek
    try:
        mgw = ManagerGameWeek.objects.get(gw=current_gameweek, manager=manager)
    except:
        return False, "Invalid gameweek"
    message = None
    virdict = False
    if not manager:
        message = "You do not have manager profile"
        virdict = False
    elif mgw.benched.all().count() < min_benched_player:
        message = f"Benched player is less than {min_benched_player}"
        virdict = True
    return virdict, message


def check_incoming_offers(manager: Manager):
    message = None
    if TransferOffer.objects.filter(to_manager=manager).count():
        virdict = True
    else:
        virdict = False
    return virdict


def player_buy_pre_validation(manager, player, offer=False):
    message = None
    virdict = False
    if not manager:
        manager_create_url = reverse_lazy('game:create_manager')
        message = f"You cannot offer this player."
    elif not player:
        message = "Player does not exist!"
    elif check_deadline():
        message = f"Transfer deadline is over, please check back later."
    elif player.bought and player.bought_by == manager:
       message = f"You have already bought {player.first_name} {player.second_name}"
    elif not offer and player.bought:
        manager_url = reverse_lazy('game:manager_detail', args=[player.bought_by.id])
        message = f"{player.web_name} is already bought by <a href='{manager_url}'>{player.bought_by.name}</a>"
        message += ", make an offer instead."
    else:
        virdict = True
    
    return virdict, message


def player_buy_post_validation(manager, player, bid_value, pre_validation=True, offer=False):
    try:
        bid_value = float(bid_value)
    except:
        message = "Enter a valid bid price!"
        virdict = False
        return virdict, message, None
    if pre_validation:
        virdict, message = player_buy_pre_validation(manager, player, offer=offer)
    else:
        virdict = True
    if virdict:
        if not offer and player.base_bid > bid_value:
            virdict = False
            message = "Bid cannot be less than the base value!"
        elif not balance_validation(manager, bid_value):
            virdict = False
            message = f"You do not have sufficient balance."
            message += f"Your balance is: {round(manager_max_balance-manager.total_bid, 2)}!"
        else:
            message = f"You have successfully bought {player.first_name} {player.second_name}"
    return virdict, message, bid_value
        
    

def player_sell_pre_validation(manager, player):
    message, warning = None, None
    virdict = False
    if not manager:
        manager_create_url = reverse_lazy('game:create_manager')
        message = f"You cannot offer this player."
    elif not player:
        message = "Player does not exist!"
    elif check_deadline():
        message = f"Transfer deadline is over, please check back later."
    elif player.bought and player.bought_by == manager:
        virdict = True
        ## Add warning for unstable players
        is_valid, warning_message = team_validation(manager, out_player=player)
        if not is_valid:
            warning = warning_message
    else:
        message = f"You do not own {player.first_name} {player.second_name}"
    
    return virdict, message, warning


def player_sell_post_validation(manager, player, pre_validation=True):
    if pre_validation:
        virdict, message, _ = player_sell_pre_validation(manager, player)
    else:
        virdict = True
    message = f"You have successfully sold {player.first_name} {player.second_name}"
    return virdict, message, None


def offer_create_pre_validator(manager: Manager, to_manager,  player: Player):
    virdict, message = True, None
    if player.bought_by != to_manager:
        virdict = False
        message = "To manager do not have the player."
    elif TransferOffer.objects.filter(from_manager=manager, to_manager=to_manager, player=player).count():
        virdict = False
        message = "You have already sent an offer."
    elif not player_buy_pre_validation(manager, player, offer=True)[0]:
        virdict, message = player_buy_pre_validation(manager, player, offer=True)
    elif not player_sell_pre_validation(to_manager, player)[0]:
        virdict, message, _ = player_sell_pre_validation(to_manager, player)
    else:
        virdict = True
    if virdict:
        message = None
    return virdict, message


def offer_create_post_validator(manager: Manager, to_manager, player: Player, bid):
    virdict, message, bid_value = True, None, bid
    if player.bought_by != to_manager:
        virdict = False
        message = "To manager do not have the player."
    elif not player_buy_post_validation(manager, player, bid, offer=True)[0]:
        virdict, message, bid_value = player_buy_post_validation(manager, player, bid, offer=True)
    elif not player_sell_post_validation(to_manager, player)[0]:
        virdict, message, _ = player_sell_post_validation(to_manager, player)
    else:
        virdict = True
    if virdict:
        message = "Transfer offer sent successfully!"
    return virdict, message, bid_value


def offer_accept_validator(manager: Manager, offer: TransferOffer):
    virdict, message = True, None
    player = offer.player
    if not offer:
        virdict = False
        message = "The offer does not exist."
    elif manager != offer.to_manager:
        virdict = False
        message = "The offer was not propesed to you."
    elif not player.bought_by == manager:
        virdict = False
        message = "You do not own the player anymore. Please, discard it."
    elif not player_buy_post_validation(offer.from_manager, player, offer.bid, offer=True)[0]:
        virdict, message, bid_value = player_buy_post_validation(offer.from_manager, player, offer.bid, offer=True)
    elif not player_sell_post_validation(offer.to_manager, player)[0]:
        virdict, message, _ = player_sell_post_validation(offer.to_manager, player)
    else:
        virdict = True
    if virdict:
        message = "Player transferred successfully!"
    return virdict, message


def offer_delete_validator(manager, offer):
    virdict, message = False, "The offer was not propesed to you."
    if manager == offer.to_manager or manager == offer.from_manager:
        virdict = True
        message = None
    return virdict, message

