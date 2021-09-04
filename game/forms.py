from django import forms
from django.core.exceptions import ValidationError
from django.core import validators

from .models import Manager, ManagerGameWeek

class ManagerForm(forms.Form):
    name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder" : "Your Name",                
                "class": "form-control"
            }
        ),
        validators=[
            validators.MinLengthValidator(2, "Your name should be at least 2 characters"),
            validators.MaxLengthValidator(19, "Your name should be less than 20 characters")
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
            validators.MinLengthValidator(2, "Team name should be at least 2 characters"),
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


class PlayerSwapForm(forms.Form):
    in_player = forms.ModelChoiceField(
        queryset=None,
        empty_label="Player In",
        widget=forms.Select(
            attrs={
                "placeholder" : "Substitute",                
                "class": "form-control bg-dark"
            }
        ),
    )

    out_player = forms.ModelChoiceField(
        queryset=None,
        empty_label="Player Out",
        widget=forms.Select(
            attrs={
                "placeholder" : "Swap with",                
                "class": "form-control bg-dark"
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        in_player = kwargs.pop("in_player_set")
        out_player = kwargs.pop("out_player_set")
        super().__init__(*args, **kwargs)
        self.fields["in_player"].queryset = in_player
        self.fields["out_player"].queryset = out_player
    