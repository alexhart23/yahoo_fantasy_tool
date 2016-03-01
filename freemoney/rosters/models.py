from django.db import models
from django.utils import timezone
import configs

class League(models.Model):
    def __str__(self):
        return self.league_name

    league_key = models.CharField(max_length=10, unique=True, primary_key=True)
    league_name = models.CharField(max_length=30, blank=True, null=True)
    num_teams = models.IntegerField()
    num_roster_spots = models.IntegerField()
    creation_date = models.DateTimeField('creation date', default=timezone.now)
    last_update = models.DateTimeField('last update', default=timezone.now)

class Manager(models.Model):
    def __str__(self):
        return self.manager_name

    class Meta:
        ordering = ['manager_name']

    manager_key = models.CharField(max_length=10, unique=True, primary_key=True)
    manager_name = models.CharField(max_length=30, blank=True, null=True)
    team_name = models.CharField(max_length=30, blank=True, null=True)
    creation_date = models.DateTimeField('creation date', default=timezone.now)
    last_update = models.DateTimeField('last update', default=timezone.now)

class Player(models.Model):
    def __str__(self):
        return self.full_name

    class Meta:
        ordering = ['last_name','first_name']

    player_key = models.CharField(max_length=12, unique=True, primary_key=True)
    last_name = models.CharField(max_length=30)
    first_name = models.CharField(max_length=30)
    position = models.CharField(max_length=6)
    nfl_team = models.CharField(max_length=3)
    manager = models.ForeignKey(Manager, default='FA')
    creation_date = models.DateTimeField('creation date', default=timezone.now)
    last_update = models.DateTimeField('last update', default=timezone.now)

    @property
    def full_name(self):
        return """{} {}""".format(self.first_name, self.last_name)

class PlayerStats(models.Model):
    pass

class PlayerCost(models.Model):
    def __str__(self):
        return self.player.full_name

    class Meta:
        ordering = ['player']

    player = models.OneToOneField(Player, primary_key=True)
    cost_2015 = models.IntegerField(default=1)
    cost_2016 = models.IntegerField(default=1)
    cost_2017 = models.IntegerField(default=1)
    cost_2018 = models.IntegerField(default=1)
    cost_2019 = models.IntegerField(default=1)
    drafted_year = models.IntegerField(blank=True, null=True)
    rookie_status = models.BooleanField(default=False)
    creation_date = models.DateTimeField('creation date', default=timezone.now)
    last_update = models.DateTimeField('last update', default=timezone.now)

class DraftPick(models.Model):
    def __str__(self):
        if self.pick_number:
            return '{} {}.{}'.format(str(self.year), str(self.selection_round), str(self.pick_number))

        else:
            if self.selection_round == 1:
                formatted_round = '1st'
            elif self.selection_round == 2:
                formatted_round = '2nd'
            elif self.selection_round == 3:
                formatted_round = '3rd'
            else:
                formatted_round = '{}th'.format(self.selection_round)
            return '{} {} - {}'.format(str(self.year), formatted_round, self.original_owner)

    class Meta:
        ordering = ['year', 'selection_round', 'pick_number']
        unique_together = (('original_owner', 'year', 'selection_round', 'pick_number'),)

    original_owner = models.ForeignKey(Manager, related_name='original_pick_owner')
    current_owner = models.ForeignKey(Manager, related_name='current_pick_owner', default=original_owner)
    selection_round = models.IntegerField()
    pick_number = models.IntegerField(blank=True, null=True)
    cost = models.IntegerField(blank=True, null=True)
    year = models.IntegerField(default=configs.year)
    player = models.OneToOneField(Player, blank=True, null=True)
    creation_date = models.DateTimeField('creation date', default=timezone.now)
    last_update = models.DateTimeField('last update', default=timezone.now)