from django import forms
from django.core.exceptions import ValidationError
from django.core import validators

from .models import Manager, Player

class ManagerForm(forms.Form):
    name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder" : "Your Name",                
                "class": "form-control"
            }
        ),
        validators=[
            validators.MinLengthValidator(2, "Your name should be at least 1 characters"),
            validators.MaxLengthValidator(49, "Your name should be less than 50 characters")
        ]
    )
    team_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder" : "Team Name",                
                "class": "form-control"
            }
        ),
        validators=[
            validators.MinLengthValidator(2, "Team name should at least 2 characters"),
            validators.MaxLengthValidator(49, "Team name should be less than 50 characters")
        ]
    )

    def clean_name(self):
        name = self.cleaned_data["name"]
        if Manager.objects.filter(name=name).exists():
            raise ValidationError("Name already exists")
        return name
    
    def clean_team_name(self):
        team_name = self.cleaned_data["team_name"]
        if Manager.objects.filter(team_name=team_name).exists():
            raise ValidationError("Team name already exists")
        return team_name



class PlayerBuyForm(forms.Form):
    bid = forms.FloatField(
        widget=forms.TextInput(
            attrs={
                "placeholder" : "Your Bid",                
                "class": "form-control"
            }
        ),
    )