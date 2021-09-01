import json

from django.shortcuts import render
from django.views.generic import View, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Q
from django.contrib.auth import get_user_model

from game.models import Manager
from .forms import ProfileForm

User = get_user_model()


class IndexView(View):
    def get(self, request):
        return render(request, "home/index.html")


class CreditView(View):
    def get(self, request):
        return render(request, "home/credits.html")


class ProfileView(LoginRequiredMixin, View):

    allowed_fields = ["id", "username", "first_name", "last_name", "email", "phone_number",
              "about_me", "facebook_link", "fpl_id", "linkedin_link"]

    def get(self, request):
        user = User.objects.get(pk=request.user.id)
        if request.POST:
            form = ProfileForm(request.POST, instance=request.user)
        else:
            form = ProfileForm(instance=user)
        context = {"user": user, "form": form, "msg": None, "success": True}
        return render(request, template_name="home/profile.html", context=context)
    
    def post(self, request):
        form = ProfileForm(request.POST or None, instance=request.user)
        msg = None
        current_user = User.objects.get(pk=request.user.id)
        try:
            if form.is_valid():
                for k,v in form.cleaned_data.items():
                    if not k in self.allowed_fields:
                        continue
                    if v!=getattr(current_user,k):
                        setattr(current_user, k, v)
                current_user.save()
                form = ProfileForm(instance=current_user)
                msg = "Profile updated successfully!"
                context = {"user": current_user, "form": form, "msg": msg, "success": True}    
                return render(request, template_name="home/profile.html", context=context)
            else:
                d = json.loads(form.errors.as_json())
                e_list = [j["message"] for i in d.values() for j in i]
                e_list = e_list if len(e_list)<2 else e_list[:2]
                msg = ", ".join(e_list)
        except Exception as e:
            msg = repr(e)

        form = ProfileForm(request.POST, instance=request.user)
        return render(request, 
                      "home/profile.html", 
                      {"form": form, "user": current_user, "msg" : msg, "success": False}
                     )
