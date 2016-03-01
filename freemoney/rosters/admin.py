from django.contrib import admin
from .models import League, Manager, Player, PlayerStats, PlayerCost, DraftPick

# Register your models here.
admin.site.register(League)
admin.site.register(Manager)
admin.site.register(Player)
admin.site.register(PlayerStats)
admin.site.register(PlayerCost)
admin.site.register(DraftPick)
