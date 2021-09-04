from django.urls import path, include, reverse_lazy
from django.views.generic.base import RedirectView

from .views import ProfileView, IndexView, CreditView, RuleView

app_name = "home"
urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("profile", ProfileView.as_view(), name="profile"),
    path("credits", CreditView.as_view(), name="credits"),
    path("rules", RuleView.as_view(), name="rules"),
]
