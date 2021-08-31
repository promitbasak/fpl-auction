from django.urls import path
from .views import login_view, register_user, CustomLogoutView
from django.contrib.auth.views import LogoutView

app_name = "accounts"
urlpatterns = [
    path('login/', login_view, name="login"),
    path('register/', register_user, name="register"),
    path("logout/", CustomLogoutView.as_view(), name="logout")
]
