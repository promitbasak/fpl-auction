from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import render, redirect


class ManagerRequiredMixin(PermissionRequiredMixin):
    login_url = reverse_lazy("game:create_manager")
    permission_denied_message = "You need to create a manager profile first!"

    def has_permission(self):
        return self.request.user.is_manager
    
    def handle_no_permission(self):
        self.request.session["manager_error_message"] = "You need to create a manager profile first!"
        return redirect(to=self.login_url)


class LeagueManagerRequiredMixin(PermissionRequiredMixin):
    login_url = reverse_lazy("home:index")
    permission_denied_message = "Only league manager can access this!"

    def has_permission(self):
        if not self.request.user.is_manager:
            return False
        return self.request.user.manager.is_league_manager
    
    def handle_no_permission(self):
        self.request.session["league_manager_error_message"] = "Only league manager can access this!"
        return redirect(to=self.login_url)
