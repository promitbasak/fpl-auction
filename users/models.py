from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
class CRMUser(AbstractUser):
    picture_url = models.URLField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True, default=None)
    is_manager = models.BooleanField(blank=True, default=False)
    about_me = models.CharField(max_length=3000, null=True, blank=True)
    facebook_link = models.CharField(max_length=100, null=True, blank=True)
    fpl_id = models.BigIntegerField(null=True, blank=True)
    linkedin_link = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.username}"
