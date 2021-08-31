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
    path("players/<int:pk>/transfer", PlayerTransferView.as_view(), name="player_transfer"),

    path("managers/", ManagerList.as_view(), name="manager_list"),
    path("managers/<int:pk>", ManagerDetail.as_view(), name="manager_detail"),
    path("managers/create", ManagerCreate.as_view(), name="create_manager"),
]
