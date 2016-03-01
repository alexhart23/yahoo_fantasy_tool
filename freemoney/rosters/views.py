from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
import configs

import rosters.models as models

# Create your views here.
def index(request):
    return render(request, 'rosters/index.html')

def rosters(request):
    managers = models.Manager.objects.all()
    context = {
        'managers': managers,
    }
    return render(request, 'rosters/rosters.html', context)

def roster_detail(request, manager_key):
    manager = models.Manager.objects.get(manager_key=manager_key)
    players = models.PlayerCost.objects.filter(player__manager_id=manager_key)
    picks = models.DraftPick.objects.filter(current_owner_id=manager_key,
                                            year__gte=configs.year,
                                            player_id__isnull=True)
    years = (2015,2016,2017,2018,2019)
    context = {
        'manager': manager,
        'players': players,
        'picks': picks,
        'years': years,
    }
    return render(request, 'rosters/roster_detail.html', context)

def allplayers(request):
    players = models.PlayerCost.objects.all()
    years = (2015,2016,2017,2018,2019)
    context = {
        'players': players,
        'years': years,
    }
    return render(request, 'rosters/allplayers.html', context)

def draftpicks(request):
    years = models.DraftPick.objects.values('year').distinct().order_by('year')
    context = {
        'years': years,
    }
    return render(request, 'rosters/draftpicks.html', context)

def draftpicks_detail(request, year):
    draftpicks = models.DraftPick.objects.filter(year=year)
    context = {
        'draftpicks': draftpicks,
        'year': year,
    }
    return render(request, 'rosters/draftpicks_detail.html', context)