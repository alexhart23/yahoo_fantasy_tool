import json
import math

import rauth
from django.core.management.base import BaseCommand
from rosters.models import League, Manager, Player, PlayerCost, DraftPick
import csv
import configs


class Command(BaseCommand):
    help = 'Download/calculate player data and load it to the DB'

    def login(self):
        request_token_url = 'https://api.login.yahoo.com/oauth/v2/get_request_token'
        authorize_url = 'https://api.login.yahoo.com/oauth/v2/request_auth'
        access_token_url = 'https://api.login.yahoo.com/oauth/v2/get_token'

        yahoo = rauth.OAuth1Service(consumer_key=configs.OAUTH_CONSUMER_KEY,
                                    consumer_secret=configs.OAUTH_SHARED_SECRET,
                                    name='yahoo',
                                    access_token_url=access_token_url,
                                    authorize_url=authorize_url,
                                    request_token_url=request_token_url,
                                    base_url='https://api.login.yahoo.com/oauth/v2/')

        request_token, request_token_secret = yahoo.get_request_token \
            (data={'oauth_callback': 'http://127.0.0.1/'})

        print("Request Token:")
        print(" - oauth_token = %s" % request_token)
        print(" - oauth_token_secret = %s" % request_token_secret)
        auth_url = yahoo.get_authorize_url(request_token)
        print('Visit this URL in your browser: ' + auth_url)

        pin = input('Enter PIN from browser: ')

        session = yahoo.get_auth_session(request_token,
                                         request_token_secret,
                                         method='POST',
                                         data={'oauth_verifier': pin})
        return session

    def get_league_info(self, session):
        print("Getting league info...")
        url = 'http://fantasysports.yahooapis.com/fantasy/v2/leagues;league_keys={league_key}/settings'.format(
            league_key=configs.league_key)
        json_string = session.get(url, params={'format': 'json'}).content
        parsed_json = json.loads(json_string.decode('utf8'))
        num_teams = parsed_json['fantasy_content']['leagues']['0']['league'][0]['num_teams']

        # get starting positions
        positions = {}
        # print(parsed_json['fantasy_content']['leagues']['0']['league'][1]['settings'][0]['roster_positions'][1]['roster_position']['position'])
        for i in parsed_json['fantasy_content']['leagues']['0']['league'][1]['settings'][0]['roster_positions']:
            positions[i['roster_position']['position']] = i['roster_position']['count']

        num_roster_spots = sum([i for i in positions.values() if type(i) != str])
        league_name = "Free Money2"

        league, create = League.objects.update_or_create(league_key=configs.league_key,
                                                         defaults={'league_name': league_name,
                                                                   'num_teams': num_teams,
                                                                   'num_roster_spots': num_roster_spots})
        league.save()



    # this only needs to be run once after the draft
    def get_cost(self, session):
        print("Assign $1 to everyone in Player table...")
        players = Player.objects.all()
        for player in players:
            #TODO update the cost variable each year
            player, create = PlayerCost.objects.get_or_create(player_id=player.player_key,
                                                              defaults={'cost_2015':1})
            player.save()

        print("Getting auction values...")

        league = League.objects.get(league_key=configs.league_key)
        league_key = league.league_key

        url = 'http://fantasysports.yahooapis.com/fantasy/v2/leagues;league_keys={league_key}/draftresults'.format(league_key=league_key)
        json_string = session.get(url, params={'format': 'json'}).content
        parsed_json = json.loads(json_string.decode('utf8'))
        # print(parsed_json['fantasy_content']['leagues']['0']['league'][1]['draft_results']['170']['draft_result']['player_key'])
        num_drafted = parsed_json['fantasy_content']['leagues']['0']['league'][1]['draft_results']['count']

        for i in range(0, num_drafted):
            player_key = parsed_json['fantasy_content']['leagues']['0']['league'][1]['draft_results'][str(i)]['draft_result']['player_key']
            cost = parsed_json['fantasy_content']['leagues']['0']['league'][1]['draft_results'][str(i)]['draft_result']['cost']

            #TODO update the cost variable each year
            PlayerCost.objects.filter(player_id=player_key).update(cost_2015=cost)

    @property
    def calculate_years_range(self, current_year=configs.year):
        years = [current_year]
        while len(years) < configs.years_in_future:
            years.append(years[-1]+1)
        return years

    def calculate_future_salaries(self, player_key, current_cost=1, current_year=configs.year):
        cost = int(current_cost)
        print(player_key)
        player = PlayerCost.objects.get(player_id=player_key)

        if player.rookie_status is True:
            salaries = [current_cost]
            # rookie contracts last 4 years. first cost is already added, so skip one
            remaining_years = (int(player.drafted_year) + 3) - current_year
            for x in range(remaining_years):
                salaries.append(cost)
            # TODO figure out expected franchise cost
            # hard coding $32 for now
            salaries.append(32)
            while len(salaries) < configs.years_in_future:
                cost = math.ceil(int(salaries[-1]) * 1.2)
                salaries.append(cost)
            return salaries
        else:
            salaries = [current_cost]
            while len(salaries) < configs.years_in_future:
                if math.ceil(cost * .2) <= 5:
                    cost = int(salaries[-1]) + 5
                else:
                    cost = math.ceil(int(salaries[-1]) * 1.2)
                salaries.append(cost)
            return salaries

    def compile_future_salaries(self):
        print("Compiling future salaries...")
        players = PlayerCost.objects.all()

        for player in players:
            #TODO update year
            starting_cost = player.cost_2015
            salaries = self.calculate_future_salaries(player.player_id, starting_cost)
            PlayerCost.objects.filter(player_id=player.player_id).update(cost_2015=salaries[0],
                                                                         cost_2016=salaries[1],
                                                                         cost_2017=salaries[2],
                                                                         cost_2018=salaries[3],
                                                                         cost_2019=salaries[4])

    def get_current_rosters(self, session):
        print("Getting current rosters...")

        league = League.objects.get(league_key=configs.league_key)
        num_teams = league.num_teams
        league_key = league.league_key

        # clear out the existing data from current_rosters

        #c.execute("DELETE from current_rosters")

        for team in range(1, num_teams + 1):
            url = 'http://fantasysports.yahooapis.com/fantasy/v2/teams;team_keys={league_key}.t.{team}/roster'.format(
                league_key=league_key, team=str(team))
            json_string = session.get(url, params={'format': 'json'}).content
            parsed_json = json.loads(json_string.decode('utf8'))
            manager_key = parsed_json['fantasy_content']['teams']['0']['team'][0][0]['team_key']
            count = parsed_json['fantasy_content']['teams']['0']['team'][1]['roster']['0']['players']['count']
            players = parsed_json['fantasy_content']['teams']['0']['team'][1]['roster']['0']['players']
            for i in range(0, count):
                player_key = players[str(i)]['player'][0][0]['player_key']

                #player, create = Player.objects.update_or_create(manager_id='')
                #player.save()
                player, create = Player.objects.update_or_create(player_key=player_key,
                                                                 defaults={'manager_id':manager_key})
                player.save()


    def get_managers(self, session):
        print("Getting manager info...")

        league = League.objects.get(league_key=configs.league_key)
        num_teams = league.num_teams
        league_key = league.league_key

        # not starting with 0 in range, so need to add 1 to total teams
        for team in range(1, num_teams + 1):
            url = 'http://fantasysports.yahooapis.com/fantasy/v2/teams;team_keys={league_key}.t.{team}'.format(
                league_key=league_key, team=str(team))
            json_string = session.get(url, params={'format': 'json'}).content
            parsed_json = json.loads(json_string.decode('utf8'))
            manager_key = parsed_json['fantasy_content']['teams']['0']['team'][0][0]['team_key']
            team_name = parsed_json['fantasy_content']['teams']['0']['team'][0][2]['name']
            manager_name = parsed_json['fantasy_content']['teams']['0']['team'][0][15]['managers'][0]['manager']['nickname']

            manager, create = Manager.objects.update_or_create(manager_key=manager_key,
                                                               defaults={'manager_name': manager_name,
                                                                         'team_name': team_name})
            manager.save()


    #def get_stats(self):
    #    check_db()
    #    print("Getting YTD points...")
    #
    #    conn = sqlite3.connect(configs.db_name)
    #    c = conn.cursor()
    #    c.execute("SELECT player_key FROM players")
    #    keys = []
    #    for row in c:
    #        keys.append(row[0])
    #    for player_key in keys:
    #        url = 'http://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/players;player_keys={player_key}/stats'.format(
    #            league_key=configs.league_key, player_key=player_key)
    #        json_string = session.get(url, params={'format': 'json'}).content
    #        parsed_json = json.loads(json_string.decode('utf8'))
    #        points = parsed_json['fantasy_content']['league'][1]['players']['0']['player'][1]['player_points']['total']
    #        try:
    #            #print("Trying to add {}, {} to table".format(player_key, points))
    #            c.execute(
    #                """INSERT OR REPLACE INTO stats (player_key, points) VALUES ("{}", {})""".format(
    #                    player_key, points))
    #        except sqlite3.IntegrityError:
    #            print('ERROR: Player Key \'{}\' already exists'.format(player_key))
    #    conn.commit()
    #    conn.close()


    def get_player_info(self, session):
        print("Getting player info...")

        players = Player.objects.all()
        for player in players:
            url = 'http://fantasysports.yahooapis.com/fantasy/v2/player/{player_key}'.format(player_key=player.player_key)
            json_string = session.get(url, params={'format': 'json'}).content
            parsed_json = json.loads(json_string.decode('utf8'))
            last_name = parsed_json['fantasy_content']['player'][0][2]['name']['last']
            first_name = parsed_json['fantasy_content']['player'][0][2]['name']['first']
            for i in parsed_json['fantasy_content']['player'][0]:
                if 'display_position' in i:
                    index = parsed_json['fantasy_content']['player'][0].index(i)
                    position = parsed_json['fantasy_content']['player'][0][index]['display_position']
                elif 'editorial_team_abbr' in i:
                    index = parsed_json['fantasy_content']['player'][0].index(i)
                    nfl_team = parsed_json['fantasy_content']['player'][0][index]['editorial_team_abbr']
            Player.objects.filter(player_key=player.player_key).update(last_name=last_name,
                                                                       first_name=first_name,
                                                                       position=position,
                                                                       nfl_team=nfl_team)
    def add_rookie_picks(self):
        print("Adding rookie pick info to DB")
        managers = Manager.objects.all()

        for manager in managers:
            #TODO change year
            for year in [2017]:
                for selection_round in [1, 2, 3]:
                    pick, create = DraftPick.objects.get_or_create(original_owner_id=manager.manager_key,
                                                                   year=year,
                                                                   selection_round=selection_round,
                                                                   defaults={'current_owner_id':manager.manager_key})
                    pick.save()

        #print("Adding previous rookie picks from csv...")
        #rows = csv.DictReader(open('rookies.{league_key}.csv'.format(league_key=configs.league_key)))
        #
        #for row in rows:
        #    pick, create = DraftPick.objects.get_or_create(player_id=row['player_key'],
        #                                                   cost=row['cost'],
        #                                                   year=row['year'],
        #                                                   selection_round=row['selection_round'],
        #                                                   pick_number=row['pick_number'],
        #                                                   original_owner_id=row['original_owner'])
        #    pick.save()

    # TODO should fix this so it doesn't readd rookie status for players that weren't kept
    def rookie_status_default(self):
        rookies = DraftPick.objects.all()

        for rookie in rookies:
            print("Updating rookie {}".format(rookie.player_id))
            PlayerCost.objects.filter(player_id=rookie.player_id).update(drafted_year=rookie.year,
                                                                         rookie_status=True)

    def handle(self, *args, **options):
        session = self.login()
        self.get_league_info(session)
        self.get_managers(session)
        self.get_current_rosters(session)
        self.get_player_info(session)
        self.get_cost(session)
        #self.rookie_status_default()
        self.compile_future_salaries()
        #self.add_rookie_picks()
