from django import forms
from django.core.exceptions import ValidationError
from django.core import validators
from django.contrib.auth import get_user_model


User = get_user_model()

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "phone_number",
              "about_me", "facebook_link", "fpl_id", "linkedin_link"]
        widgets = {
            "username": forms.TextInput(attrs={'placeholder': 'Username', 
                                        "class": "form-control"}),
            "first_name": forms.TextInput(attrs={'placeholder': 'First Name',
                                                 "class": "form-control"}),
            "last_name": forms.TextInput(attrs={'placeholder': 'Last Name',
                                                "class": "form-control"}),
            "email": forms.EmailInput(attrs={'placeholder': 'Email Address',
                                             "class": "form-control"}),
            "phone_number": forms.TextInput(attrs={'placeholder': 'Phone Number', 
                                                     "class": "form-control"}),
            "about_me": forms.Textarea(attrs={'placeholder': 'Write about you...', 
                                              "class": "form-control", "rows":4, "cols":80}),
            "facebook_link": forms.TextInput(attrs={'placeholder': 'Link to your profile', 
                                                   "class": "form-control"}),
            "fpl_id": forms.NumberInput(attrs={'placeholder': 'Numeric FPL ID',
                                               "class": "form-control"}),
            "linkedin_link": forms.TextInput(attrs={'placeholder': 'Link to your profile', 
                                                   "class": "form-control"}),
        }
    
    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise ValidationError(f"Email already exists!")
        return email
    
    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
            raise ValidationError(f"Username already exists!")
        return username
    
    def clean_facebook_link(self):
        facebook_link = self.cleaned_data["facebook_link"]
        if facebook_link and not facebook_link.startswith("http"):
            facebook_link = "https://" + facebook_link
        return facebook_link
    

    def clean_linkedin_link(self):
        linkedin_link = self.cleaned_data["linkedin_link"]
        if linkedin_link and not linkedin_link.startswith("http"):
            linkedin_link = "https://" + linkedin_link
        return linkedin_link