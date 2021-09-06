import json

from django.views.generic import View, ListView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import AuctionBid, Player, Manager, TransferHistory, Team, PlayerType, Parameters, TransferOffer
from .forms import ManagerForm, PlayerBuyForm, PlayerSwapForm
from .mixins import ManagerRequiredMixin, LeagueManagerRequiredMixin
from .validators import (
    auction_bid_create_pre_validation,
    player_buy_post_validation, 
    player_buy_pre_validation,
    player_sell_pre_validation,
    player_sell_post_validation,
    auction_player_bid_pre_validation,
    check_deadline,
    offer_create_pre_validator,
    player_sell_post_validation,
    player_sell_pre_validation,
    squad_validation,
    check_auction_finished,
)
from .utils import (
    add_warning_to_offers,
    commit_auction_approve,
    commit_auction_bid,
    commit_auction_create,
    commit_offer_accept,
    commit_offer_create,
    commit_offer_discard,
    commit_player_buy, 
    commit_player_sell, 
    commit_create_manager,
    commit_player_swap, 
    get_all_squad_players,
    get_auction_bid, 
    get_next_deadline,
    dict_to_object,
    squad_truncate
)
from .constants import manager_max_balance


User = get_user_model()

class IndexView(LoginRequiredMixin, View):
    def get(self, request):
        return redirect(reverse_lazy("game:player_list"))


class ProfileView(LoginRequiredMixin, View):
    pass


class PlayerList(LoginRequiredMixin, ListView):
    model = Player
    filterset_fields = ["team", "position", "search", "orderby"]
    ordering_fields = ["web_name", "total_points", "selected_by_percent", "now_cost"]
    ordering_field_names = ["Name", "Points", "Selected by", "Price"]
    paginate_by = 30

    def get_queryset(self):
        queryset = super().get_queryset().all()
        filters = {k:v for k,v in self.request.GET.items() if k in self.filterset_fields}
        if "team" in filters:
            queryset = queryset.filter(team__id=filters["team"])
        if "position" in filters:
            queryset = queryset.filter(element_type__id=filters["position"])
        if "search" in filters:
            queryset = queryset.filter(web_name__contains=filters["search"])
        if "orderby" in filters and filters["orderby"] in self.ordering_fields:
            if filters["orderby"] in ["total_points", "selected_by_percent"]:
                queryset = queryset.order_by("-" + filters["orderby"])
            else:
                queryset = queryset.order_by(filters["orderby"])
        else:
            queryset = queryset.order_by("web_name")
        return queryset
    

    def get_context_data(self, **kwargs):
        filters = {k:v for k,v in self.request.GET.items() if k in self.filterset_fields}
        context = super().get_context_data(**kwargs)
        context["teams"] = dict(Team.objects.all().values_list("id", "name"))
        context["positions"] = dict(PlayerType.objects.all().values_list("id", "position_verbose"))
        context["sorting_fields"] = dict(zip(self.ordering_fields, self.ordering_field_names))
        filters = {k:v for k,v in self.request.GET.items() if k in self.filterset_fields}
        context["current_team"] = int(self.request.GET.get("team")) if "team" in filters else None
        context["current_position"] = int(self.request.GET.get("position")) if "position" in filters else None
        context["current_search"] = self.request.GET.get("search") if "search" in filters else None
        if "orderby" in filters and filters["orderby"] in self.ordering_fields:
            context["current_orderby"] = self.request.GET.get("orderby")
        else:
            context["current_orderby"] = "web_name"
        return context
    
    def get_template_names(self):
        return ["game/players.html"]
    


class PlayerDetail(LoginRequiredMixin, DetailView):
    model = Player


class ManagerList(LoginRequiredMixin, ListView):
    model = Manager
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset().order_by("-total_points")

    def get_template_names(self):
        return ["game/managers.html"]



class ManagerDetail(LoginRequiredMixin, DetailView):
    model = Manager

    def get_context_data(self, **kwargs):
        context = super(ManagerDetail, self).get_context_data(**kwargs)
        context["manager_max_balance"] = manager_max_balance
        return context



class ManagerCreate(LoginRequiredMixin, View):
    template_path = "game/manager_create.html"

    def get(self, request):
        msg, success = None, True
        form = ManagerForm(request.POST or None)
        if request.session.get("manager_error_message"):
            msg = request.session.pop("manager_error_message")
            success = False
        if request.user.is_manager:
            msg = "You are already a manager"
            form, success = None, False
        context = {"form": form, "msg": msg, "success": success}
        return render(request, self.template_path, context=context)
    
    def post(self, request):
        msg, success = None, False
        form = ManagerForm(request.POST or None)
        if request.user.is_manager:
            msg = "You are already a manager"
            form = None
        elif form.is_valid():
            name = form.cleaned_data.get("name")
            team_name = form.cleaned_data.get("team_name")
            commit_create_manager(request.user, name, team_name)
            form, success = None, True
            msg = "Manager profile created successfully. <br/> Now you can explore and trade players."
        else:
            d = json.loads(form.errors.as_json())
            e_list = [j["message"] for i in d.values() for j in i]
            e_list = e_list if len(e_list)<2 else e_list[:2]
            msg = ", ".join(e_list)
        context = {"form": form, "msg": msg, "success": success}
        return render(request, self.template_path, context=context)
        


class PlayerBuyView(LoginRequiredMixin, ManagerRequiredMixin, View):
    template_path = "game/player_buy.html"

    def get(self, request, pk):
        manager = request.user.manager
        player = Player.objects.filter(pk=pk).first()
        success, msg = player_buy_pre_validation(manager, player)
        form = PlayerBuyForm(initial={"bid": player.base_bid}) if success else None
        context = {"form": form, "msg" : msg, "success": success, "player": player}
        return render(request, self.template_path, context=context)

    def post(self, request, pk):
        manager = request.user.manager
        player = Player.objects.filter(pk=pk).first()
        bid_value = request.POST.get("bid")
        success, msg, bid_value = player_buy_post_validation(manager, player, bid_value)
        form = PlayerBuyForm(request.POST or None)
        if success:
            commit_player_buy(manager, player, bid_value)
            player, form = None, None
        context = {"form": form, "msg" : msg, "success": success, "player": player}
        return render(request, self.template_path, context=context)


        
class PlayerSellView(LoginRequiredMixin, ManagerRequiredMixin, View):
    template_path = "game/player_sell.html"

    def get(self, request, pk):
        manager = request.user.manager
        player = Player.objects.filter(pk=pk).first()
        warning = None
        success, msg, warning = player_sell_pre_validation(manager, player) 
        form = PlayerBuyForm() if success else None
        context = {"form": form, "msg" : msg, "success": success, "player": player, "warning": warning}
        return render(request, self.template_path, context=context)

    def post(self, request, pk):
        manager = request.user.manager
        player = Player.objects.filter(pk=pk).first()
        success, msg, warning = player_sell_post_validation(manager, player)
        form = PlayerBuyForm(request.POST or None)
        if success:
            bid_value = player.current_bid
            added = commit_player_sell(manager, player, bid_value)
            player, form = None, None
        context = {"form": form, "msg" : msg, "success": success, "player": player}
        return render(request, self.template_path, context=context)



class OfferView(LoginRequiredMixin, ManagerRequiredMixin, View):
    template_path = "game/offer_list.html"

    def get(self, request):
        in_msg, in_success, out_msg, out_success = None, False, None, False
        if request.session.get("in_offer_accept_message"):
            in_msg = request.session.pop("in_offer_accept_message")
            in_success = request.session.pop("in_offer_accept_state")
        elif request.session.get("out_offer_accept_message"):
            out_msg = request.session.pop("out_offer_accept_message")
            out_success = request.session.pop("out_offer_accept_state") 
        sent = TransferOffer.objects.filter(from_manager=self.request.user.manager).order_by("-id")
        received = TransferOffer.objects.filter(to_manager=self.request.user.manager).order_by("-id")
        warnings, is_valids = add_warning_to_offers(received)
        context = {"sent": sent, "received": received, "in_msg": in_msg, "in_success": in_success,
            "out_msg": out_msg, "out_success": out_success, "warnings":warnings, "is_valids": is_valids}
        return render(request, self.template_path, context=context)



class PlayerOfferCreateView(LoginRequiredMixin, ManagerRequiredMixin, View):
    template_path = "game/offer_create.html"

    def get(self, request, pk):
        manager = request.user.manager
        player = Player.objects.filter(pk=pk).first()
        to_manager = player.bought_by
        success, msg = offer_create_pre_validator(manager, to_manager, player)
        form = PlayerBuyForm() if success else None
        context = {"form": form, "msg" : msg, "success": success, "player": player}
        return render(request, self.template_path, context=context)

    def post(self, request, pk):
        manager = request.user.manager
        player = Player.objects.filter(pk=pk).first()
        to_manager = player.bought_by
        bid_value = request.POST.get("bid")
        success, msg = commit_offer_create(manager, to_manager, player, bid_value)
        form = PlayerBuyForm(request.POST or None)
        if success:
            player, form = None, None
        context = {"form": form, "msg" : msg, "success": success, "player": player}
        return render(request, self.template_path, context=context)


class OfferAcceptView(LoginRequiredMixin, ManagerRequiredMixin, View):
    template_path = "game/offer_list.html"

    def post(self, request):
        manager = request.user.manager
        offer_id = request.POST.get("offer_id")
        offer = TransferOffer.objects.filter(pk=offer_id).first()
        success, msg = commit_offer_accept(manager, offer)
        if offer.to_manager == request.user.manager:
            self.request.session["in_offer_accept_message"] = msg
            self.request.session["in_offer_accept_state"] = success
        else:
            self.request.session["out_offer_accept_message"] = msg
            self.request.session["out_offer_accept_state"] = success
        return redirect(to=reverse_lazy("game:offer_list"))


class OfferDiscardView(LoginRequiredMixin, ManagerRequiredMixin, View):
    template_path = "game/offer_list.html"

    def post(self, request):
        manager = request.user.manager
        offer_id = request.POST.get("offer_id")
        print(offer_id, type(offer_id))
        offer = TransferOffer.objects.filter(pk=offer_id).first()
        success, msg = commit_offer_discard(manager, offer)
        if offer.to_manager == request.user.manager:
            self.request.session["in_offer_accept_message"] = msg
            self.request.session["in_offer_accept_state"] = success
        else:
            self.request.session["out_offer_accept_message"] = msg
            self.request.session["out_offer_accept_state"] = success
        return redirect(to=reverse_lazy("game:offer_list"))



class SquadView(LoginRequiredMixin, ManagerRequiredMixin, View):
    template_path = "game/manage_team.html"

    def get(self, request):
        if check_deadline():
            squad_truncate(request.user.manager)
        players = get_all_squad_players(request.user.manager)
        deadline = check_deadline()
        next_deadline = get_next_deadline()
        msg = "Substitute deadline is over, please check back later" if deadline else None
        success = False if deadline else True
        form = (None if deadline else 
                    PlayerSwapForm(in_player_set=players["benched"], out_player_set=players["squad"]))
        context = {"players": dict_to_object(players), "form": form, "success": success, "msg": msg,
                     "next_deadline": next_deadline}
        return render(request, self.template_path, context=context)

    def post(self, request):
        success, msg = True, None
        deadline = check_deadline()
        if deadline:
            success = False
            msg = "Substitute deadline is over, please check back later"
        else:
            in_player, out_player = request.POST.get("in_player"), request.POST.get("out_player")
            in_player = Player.objects.filter(pk=in_player).first()
            out_player = Player.objects.filter(pk=out_player).first()
            if in_player and out_player:
                success, msg = commit_player_swap(request.user.manager, in_player, out_player)
            else:
                success = False
                msg = "Select both player in and player out!"
        players = get_all_squad_players(request.user.manager)
        form = (None if deadline else 
                    PlayerSwapForm(in_player_set=players["benched"], out_player_set=players["squad"]))
        next_deadline = get_next_deadline()
        context = {"players": dict_to_object(players), "form": form, "success": success, "msg": msg,
                     "next_deadline": next_deadline}
        return render(request, self.template_path, context=context)
            


class TransferHistoryList(LoginRequiredMixin, ListView):
    model = TransferHistory
    paginate_by = 30

    def get_queryset(self):
        return super().get_queryset().order_by("-time")

    def get_template_names(self):
        return ["game/transfer_history.html"]



class AuctionListView(LoginRequiredMixin, LeagueManagerRequiredMixin, ListView):
    model = Player
    filterset_fields = ["team", "position", "search", "orderby"]
    ordering_fields = ["web_name", "total_points", "selected_by_percent", "now_cost"]
    ordering_field_names = ["Name", "Points", "Selected by", "Price"]
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset().filter(~Q(bought=True))
        filters = {k:v for k,v in self.request.GET.items() if k in self.filterset_fields}
        if "team" in filters:
            queryset = queryset.filter(team__id=filters["team"])
        if "position" in filters:
            queryset = queryset.filter(element_type__id=filters["position"])
        if "search" in filters:
            queryset = queryset.filter(web_name__contains=filters["search"])
        if "orderby" in filters and filters["orderby"] in self.ordering_fields:
            if filters["orderby"] in ["total_points", "selected_by_percent"]:
                queryset = queryset.order_by("-" + filters["orderby"])
            else:
                queryset = queryset.order_by(filters["orderby"])
        else:
            queryset = queryset.order_by("web_name")
        return queryset
    

    def get_context_data(self, **kwargs):
        filters = {k:v for k,v in self.request.GET.items() if k in self.filterset_fields}
        context = super().get_context_data(**kwargs)
        context["teams"] = dict(Team.objects.all().values_list("id", "name"))
        context["positions"] = dict(PlayerType.objects.all().values_list("id", "position_verbose"))
        context["sorting_fields"] = dict(zip(self.ordering_fields, self.ordering_field_names))
        filters = {k:v for k,v in self.request.GET.items() if k in self.filterset_fields}
        context["current_team"] = int(self.request.GET.get("team")) if "team" in filters else None
        context["current_position"] = int(self.request.GET.get("position")) if "position" in filters else None
        context["current_search"] = self.request.GET.get("search") if "search" in filters else None
        if "orderby" in filters and filters["orderby"] in self.ordering_fields:
            context["current_orderby"] = self.request.GET.get("orderby")
        else:
            context["current_orderby"] = "web_name"
        if self.request.session.get("auction_create_msg"):
            context["msg"] = self.request.session.pop("auction_create_msg")
        if self.request.session.get("auction_create_success"):
            context["success"] = self.request.session.pop("auction_create_success")
        return context
    
    def get_template_names(self):
        return ["game/auction_list.html"]



class AuctionRoomView(LoginRequiredMixin, ManagerRequiredMixin, View):
    template_path = "game/auction_room.html"

    def get(self, request):
        success, msg, approval_success, approval_msg = True, None, True, None
        finish_success, finish_msg = True, None
        auction_bid = get_auction_bid()
        sold_bids = AuctionBid.objects.filter(is_sold=True)
        form = PlayerBuyForm() if auction_bid else None
        if request.session.get("auction_approve_msg"):
            approval_msg = request.session.pop("auction_approve_msg")
            approval_success = request.session.pop("auction_approve_success")
        if request.session.get("auction_finish_msg"):
            finish_msg = request.session.pop("auction_finish_msg")
            finish_success = request.session.pop("auction_finish_success")
        context = {"auction_bid": auction_bid, "sold_bids": sold_bids, "form": form,
                    "success": success, "msg": msg, "approval_msg": approval_msg,
                    "approval_success": approval_success, "finish_msg": finish_msg,
                    "finish_success": finish_success, "manager_max_balance": manager_max_balance}
        return render(request, self.template_path, context=context)
    
    def post(self, request):
        manager = request.user.manager
        form = PlayerBuyForm(request.POST or None)
        bid_value = request.POST.get("bid")
        auction_bid_id = request.POST.get("auction_bid_id")
        auction_bid = AuctionBid.objects.filter(pk=auction_bid_id).first()
        success, msg, bid_value= auction_player_bid_pre_validation(auction_bid, bid_value)
        if success:
            success, msg, bid_value = player_buy_post_validation(manager, auction_bid.player, 
                                        bid_value, auction=True, top_bid=auction_bid.highest_bid)
        if success:
            commit_auction_bid(auction_bid, manager, bid_value)
            msg = "You have successfully placed the bid"
        sold_bids = AuctionBid.objects.filter(is_sold=True)
        auction_bid = get_auction_bid()
        context = {"auction_bid": auction_bid, "sold_bids": sold_bids, "form": form, 
                    "msg" : msg, "success": success, "manager_max_balance": manager_max_balance}
        return render(request, self.template_path, context=context)


class AuctionApproveView(LoginRequiredMixin, LeagueManagerRequiredMixin, View):
    template_path = "game/auction_room.html"

    def post(self, request):
        auction_bid = get_auction_bid()
        if check_auction_finished():
            context = {"success": False, "msg": "Auction finished!"}
            return render(request, self.template_path, context=context)
        if not auction_bid:
            context = {"success": False, "msg": "Invalid auction bid!"}
            return render(request, self.template_path, context=context)
        success, msg = commit_auction_approve(auction_bid)
        if msg:
            request.session["auction_approve_msg"] = msg
            request.session["auction_approve_success"] = success
        return redirect(to=reverse_lazy("game:auction_room"))


class AuctionCreateView(LoginRequiredMixin, LeagueManagerRequiredMixin, View):
    template_path = "game/auction_room.html"

    def post(self, request, pk):
        player = Player.objects.filter(pk=pk).first()
        success, msg = auction_bid_create_pre_validation(player)
        if success:
            commit_auction_create(player=player)
        if msg:
            request.session["auction_create_msg"] = msg
            request.session["auction_create_success"] = success
        return redirect(to=reverse_lazy("game:auction_list"))


class AuctionFinishView(LoginRequiredMixin, LeagueManagerRequiredMixin, View):
    
    def post(self, request):
        success, msg = False, None
        if check_auction_finished():
            context = {"success": False, "msg": "Auction finished!"}
            return render(request, self.template_path, context=context)
        auction_bid = get_auction_bid()
        if auction_bid:
            success, msg = commit_auction_approve(auction_bid)
        parameter = Parameters.objects.all().first()
        parameter.is_auction_finished = True
        parameter.save()
        if msg:
            request.session["auction_finish_msg"] = msg
            request.session["auction_finish_success"] = success
        for player in Player.objects.filter(~Q(bought=True)):
            player.base_bid = player.now_cost
            player.save()
        return redirect(to=reverse_lazy("game:auction_room"))


class CustomRedirectView(View):
    pass


