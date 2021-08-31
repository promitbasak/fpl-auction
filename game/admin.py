from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Team)
admin.site.register(PlayerType)
admin.site.register(PlayerStatus)
admin.site.register(Player)
admin.site.register(PlayerGameWeek)

admin.site.register(Manager)
admin.site.register(ManagerGameWeek)

admin.site.register(TransferHistory)