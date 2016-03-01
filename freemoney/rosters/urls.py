__author__ = 'Alex Hart'

from django.conf.urls import url

from . import views

app_name = 'rosters'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    # /allplayers/
    url(r'^allplayers/$', views.allplayers, name='allplayers'),
    # /rosters/
    url(r'^rosters/$', views.rosters, name='rosters'),
    # /rosters/<manager_key>/
    url(r'^rosters/(?P<manager_key>.+)/$', views.roster_detail, name='roster_detail'),
    # /draftpicks/
    url(r'^draftpicks/$', views.draftpicks, name='draftpicks'),
    # /draftpicks/<year>/
    url(r'^draftpicks/(?P<year>\d{4})/$', views.draftpicks_detail, name='draftpicks_detail'),

]