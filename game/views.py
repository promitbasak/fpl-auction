import json, math

from django.views.generic import View, CreateView, UpdateView, ListView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Q
from django.contrib.auth import get_user_model

from .models import Player, Manager, TransferHistory
from .forms import ManagerForm, PlayerBuyForm

User = get_user_model()

class IndexView(LoginRequiredMixin, View):
    def get(self, request):
        return redirect(reverse_lazy("game:player_list"))


class ProfileView(LoginRequiredMixin, View):
    pass


class PlayerList(LoginRequiredMixin, ListView):
    model = Player
    paginate_by = 60

    def get_queryset(self):
        return super().get_queryset().filter(~Q(status__status="n"))

    def get_template_names(self):
        return ["game/players.html"]
    
    


class PlayerDetail(LoginRequiredMixin, DetailView):
    model = Player


class ManagerList(LoginRequiredMixin, ListView):
    model = Manager
    paginate_by = 20

    def get_template_names(self):
        return ["game/managers.html"]



class ManagerDetail(LoginRequiredMixin, DetailView):
    model = Manager



class ManagerCreate(LoginRequiredMixin, View):
    
    def get(self, request):
        is_exists = request.user.is_manager
        form = ManagerForm(None)
        return render(request, 
                      "game/manager_create.html", 
                      {"form": form, "msg" : None, "is_exists": is_exists}
                     )
    
    def post(self, request):
        form = ManagerForm(request.POST or None)
        msg = None
        is_exists = request.user.is_manager
        if not is_exists:
            try:
                if form.is_valid():
                    name = form.cleaned_data.get("name")
                    team_name = form.cleaned_data.get("team_name")
                    manager = Manager(name=name, team_name=team_name, total_bid=0.0, user=request.user)
                    manager.save()
                    current_user = User.objects.get(pk=request.user.id)
                    current_user.is_manager = True
                    current_user.save()
                    return redirect(reverse_lazy("home:profile"))
                else:
                    d = json.loads(form.errors.as_json())
                    e_list = [j["message"] for i in d.values() for j in i]
                    e_list = e_list if len(e_list)<2 else e_list[:2]
                    msg = ", ".join(e_list)
            except Exception as e:
                msg = repr(e)
        else:
            msg = "You already have manager profile!" 
        return render(request, 
                      "game/manager_create.html", 
                      {"form": form, "msg" : msg, "is_exists": is_exists}
                     )


class PlayerBuyView(LoginRequiredMixin, View):
    def get(self, request, pk):
        try:
            player = Player.objects.get(pk=pk)
        except:
            player=None
        form = PlayerBuyForm()
        return render(request, 
                      "game/player_buy.html", 
                      {"form": form, "msg" : None, "success":False, "player":player}
                     )
    def post(self, request, pk):
        form = PlayerBuyForm(request.POST or None)
        msg = None
        player = None
        success = False
        if not request.user.is_manager:
            create_manager_url = reverse_lazy("game:create_manager")
            msg = f"<a href='{create_manager_url}'>Create you manager profile</a> first!"
            return render(request, 
                      "game/player_buy.html", 
                      {"form": form, "msg" : msg, "success": success, "player": player}
                     )
        try:
            player = Player.objects.get(pk=pk)
            try:
                bid_value = float(request.POST.get("bid"))
            except:
                msg = "Enter a valid bid price!"
                return render(request, 
                        "game/player_buy.html", 
                        {"form": form, "msg" : msg, "success": success, "player": player}
                        )
            if player.base_bid>bid_value:
                msg = "Bid cannot be less than the base value."
            elif player.bought_by and player.bought_by.id == request.user.manager.id:
                msg = "You have already bought this player."
            elif player.bought_by:
                manager_url = reverse_lazy('game:manager_detail', args=[player.bought_by.id])
                msg = f"Player is bought by <a href='{manager_url}'>{player.bought_by.name}</a>"
            else:
                manager = Manager.objects.get(pk=request.user.manager.id)
                player.bought_by = manager
                player.bought = True
                player.current_bid = bid_value
                player.save()
                msg = "Player bought successfully!"
                success = True
                trans_hist = TransferHistory(player=player, to_manager=manager, bid=bid_value, type=1)
                trans_hist.save()
                manager.total_bid += bid_value
                manager.save()
                return render(request, 
                      "game/player_buy.html", 
                      {"form": PlayerBuyForm(), "msg" : msg, "success": success, "player": player}
                     )
        except:
            msg = f"Player not found!"
        return render(request, 
                      "game/player_buy.html", 
                      {"form": form, "msg" : msg, "success": success, "player": player}
                     )
        
class PlayerSellView(LoginRequiredMixin, View):
    def get(self, request, pk):
        try:
            player = Player.objects.get(pk=pk)
        except:
            player=None
        form = PlayerBuyForm()
        return render(request, 
                      "game/player_sell.html", 
                      {"form": form, "msg" : None, "success":False, "player":player}
                     )
    def post(self, request, pk):
        form = PlayerBuyForm(request.POST or None)
        msg = None
        player = None
        success = False
        if not request.user.is_manager:
            create_manager_url = reverse_lazy("game:create_manager")
            msg = f"<a href='{create_manager_url}'>Create you manager profile</a> first!"
            return render(request, 
                      "game/player_sell.html", 
                      {"form": form, "msg" : msg, "success": success, "player": player}
                     )
        try:
            player = Player.objects.get(pk=pk)
            if not player.bought or player.bought_by.id != request.user.manager.id:
                msg = "You have not bought this player."
            else:
                manager = Manager.objects.get(pk=request.user.manager.id)
                prev_bid = player.current_bid
                player.bought_by = None
                player.bought = False
                player.current_bid = None
                player.save()
                msg = "Player sold successfully!"
                success = True
                trans_hist = TransferHistory(player=player, from_manager=manager, bid=prev_bid, type=2)
                trans_hist.save()
                manager.total_bid -= prev_bid
                manager.save()
                return render(request, 
                      "game/player_sell.html", 
                      {"form": PlayerBuyForm(), "msg" : msg, "success": success, "player": player}
                     )
        except:
            msg = f"Player not found!"
        return render(request, 
                      "game/player_sell.html", 
                      {"form": form, "msg" : msg, "success": success, "player": player}
                     )


class PlayerTransferView(LoginRequiredMixin, View):
    pass
        

class TransferHistoryList(LoginRequiredMixin, View):
    def get(self, request):
        transfers = TransferHistory.objects.all()
        context = {"list": transfers}
        return render(request, "", context=context)
