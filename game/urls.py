from django.contrib import admin
from django.contrib.admin.sites import all_sites
from django.urls import path
from django.urls.conf import include
from django.views.generic.base import RedirectView
from .views import *


app_name = "game"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),

    path("players/", PlayerList.as_view(), name="player_list"),
    path("players/<int:pk>", PlayerDetail.as_view(), name="player_detail"),
    path("players/<int:pk>/buy", PlayerBuyView.as_view(), name="player_buy"),
    path("players/<int:pk>/sell", PlayerSellView.as_view(), name="player_sell"),
    path("players/<int:pk>/offer", PlayerOfferCreateView.as_view(), name="player_offer"),

    path("manage_team/", SquadView.as_view(), name="manage_team"),
    
    path("managers/", ManagerList.as_view(), name="manager_list"),
    path("managers/<int:pk>", ManagerDetail.as_view(), name="manager_detail"),
    path("managers/create", ManagerCreate.as_view(), name="create_manager"),

    path("offers/", OfferView.as_view(), name="offer_list"),
    path("offers/accept/", OfferAcceptView.as_view(), name="offer_accept"),
    path("offers/discard/", OfferDiscardView.as_view(), name="offer_discard"),

    path("transfer_history/", TransferHistoryList.as_view(), name="transfer_history"),

    path("auction/room/", AuctionRoomView.as_view() ,name="auction_room"),
    path("auction/list/", AuctionListView.as_view(), name="auction_list"),
    path("auction/list/create/<int:pk>", AuctionCreateView.as_view(), name="auction_create"),
    path("auction/room/approve/", AuctionApproveView.as_view(), name="auction_approve"),
    path("auction/room/finish/", AuctionFinishView.as_view(), name="auction_finish"),
]
