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