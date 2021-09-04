import json, math

from django.views.generic import View, CreateView, UpdateView, ListView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Q
from django.contrib.auth import get_user_model

from .models import Player, Manager, TransferHistory, Team, PlayerType, Parameters, TransferOffer
from .forms import ManagerForm, PlayerBuyForm, PlayerSwapForm
from .validators import check_deadline, offer_create_pre_validator, player_sell_post_validation, player_sell_pre_validation, squad_validation
from .mixins import ManagerRequiredMixin
from .validators import (
    player_buy_post_validation, 
    player_buy_pre_validation,
    player_sell_pre_validation,
    player_sell_post_validation
)
from .utils import (
    add_warning_to_offers,
    commit_offer_accept,
    commit_offer_create,
    commit_offer_discard,
    commit_player_buy, 
    commit_player_sell, 
    commit_create_manager,
    commit_player_swap, 
    get_all_squad_players, 
    get_next_deadline,
    dict_to_object,
    squad_truncate
)

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
        queryset = super().get_queryset().filter(~Q(status__status="n"))
        filters = {k:v for k,v in self.request.GET.items() if k in self.filterset_fields}
        if "team" in filters:
            queryset = queryset.filter(team__id=filters["team"])
            # params = self.request.GET.copy()
            # params["page"] = 1
            # self.request.GET = params
        if "position" in filters:
            queryset = queryset.filter(element_type__id=filters["position"])
            # params = self.request.GET.copy()
            # params["page"] = 1
            # self.request.GET = params
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


class CustomRedirectView(View):
    pass
