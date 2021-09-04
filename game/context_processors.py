from .validators import check_incoming_offers, check_unstable_squad, check_unstable_team

def notifications(request):
    if request.user.is_authenticated and request.user.is_manager:
         return {
            "check_incoming_offers": check_incoming_offers(request.user.manager),
            "check_unstable_squad": check_unstable_squad(request.user.manager)[0],
            "check_unstable_team": check_unstable_team(request.user.manager)[0],
        }
    else:
        return {}