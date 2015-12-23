__author__ = 'Alex Hart'

from rauth import OAuth1Service
import json
import configs
import sqlite3
import os
import sys

if not os.path.isfile(configs.db_name):
    print("{} does not exist. Please create it with 'create_league_db.py'...".format(configs.db_name))
    sys.exit(1)


def login():
    request_token_url = 'https://api.login.yahoo.com/oauth/v2/get_request_token'
    authorize_url = 'https://api.login.yahoo.com/oauth/v2/request_auth'
    access_token_url = 'https://api.login.yahoo.com/oauth/v2/get_token'

    yahoo = OAuth1Service(consumer_key=configs.OAUTH_CONSUMER_KEY,
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


session = login()


# age

# ROS projected points

def get_league_info(session):
    print("Getting league info...")
    url = 'http://fantasysports.yahooapis.com/fantasy/v2/leagues;league_keys={league_key}/settings'.format(
        league_key=configs.league_key)
    json_string = session.get(url, params={'format': 'json'}).content
    parsed_json = json.loads(json_string.decode('utf8'))
    num_teams = parsed_json['fantasy_content']['leagues']['0']['league'][0][
        'num_teams']

    # get starting positions
    positions = {}
    # print(parsed_json['fantasy_content']['leagues']['0']['league'][1]['settings'][0]['roster_positions'][1]['roster_position']['position'])
    for i in \
            parsed_json['fantasy_content']['leagues']['0']['league'][1]['settings'][0][
                'roster_positions']:
        positions[i['roster_position']['position']] = i['roster_position'][
            'count']

    num_roster_spots = sum([i for i in positions.values() if type(i) != str])
    conn = sqlite3.connect(configs.db_name)
    c = conn.cursor()
    try:
        print("Trying to add {}, {},{} to table".format(configs.league_key,
                                                        num_teams,
                                                        num_roster_spots))
        c.execute(
            "INSERT OR REPLACE INTO league (league_key, num_teams, num_roster_spots) VALUES ('{}', {}, '{}')".format(
                configs.league_key, num_teams, num_roster_spots))
    except sqlite3.IntegrityError:
        print(
            'ERROR: League Key already exists in PRIMARY KEY column {}'.format(
                league_key))

    conn.commit()
    conn.close()

    return num_teams, positions, num_roster_spots


# this only needs to be run once after the draft
def get_auction_values(session):
    print("Getting auction values...")
    url = 'http://fantasysports.yahooapis.com/fantasy/v2/leagues;league_keys={league_key}/draftresults'.format(
        league_key=configs.league_key)
    json_string = session.get(url, params={'format': 'json'}).content
    parsed_json = json.loads(json_string.decode('utf8'))
    # print(parsed_json['fantasy_content']['leagues']['0']['league'][1]['draft_results']['170']['draft_result']['player_key'])
    num_drafted = parsed_json['fantasy_content']['leagues']['0']['league'][1][
        'draft_results']['count']

    """with open('data/auction_values.{league_key}.csv'.format(
            league_key=configs.league_key), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['player_key', 'cost'])
        for i in range(0, num_drafted):
            writer.writerow([parsed_json['fantasy_content']['leagues']['0'][
                                 'league'][1]['draft_results'][str(i)][
                                 'draft_result']['player_key'],
                             parsed_json['fantasy_content']['leagues']['0'][
                                 'league'][1]['draft_results'][str(i)][
                                 'draft_result']['cost']])"""

    conn = sqlite3.connect(configs.db_name)
    c = conn.cursor()
    for i in range(0, num_drafted):
        player_key = \
        parsed_json['fantasy_content']['leagues']['0']['league'][1]['draft_results'][str(i)]['draft_result'][
            'player_key']
        cost = parsed_json['fantasy_content']['leagues']['0']['league'][1]['draft_results'][str(i)]['draft_result'][
            'cost']
        try:
            print("Trying to add {}, {} to table".format(player_key, cost))
            c.execute(
                "INSERT OR IGNORE INTO auction_values (player_key, cost) VALUES ('{}', {})".format(player_key, cost))
        except sqlite3.IntegrityError:
            print('ERROR: Player Key already exists in PRIMARY KEY column {}'.format(player_key))
    conn.commit()
    conn.close()


def get_current_rosters(session, num_teams):
    print("Getting current rosters...")
    """with open('data/current_rosters.{league_key}.csv'.format(
            league_key=configs.league_key), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['player_key', 'team_key'])
        # not starting with 0 in range, so need to add 1 to total teams
        for team in range(1, num_teams + 1):
            url = 'http://fantasysports.yahooapis.com/fantasy/v2/teams;team_keys={league_key}.t.{team}/roster'.format(
                league_key=configs.league_key, team=str(team))
            json_string = session.get(url, params={'format': 'json'}).content
            parsed_json = json.loads(json_string.decode('utf8'))
            # need team_key, player_key, first, last, editorial_team_abbr, display_position, eligible_positions
            team_key = \
            parsed_json['fantasy_content']['teams']['0']['team'][0][0][
                'team_key']
            team_name = \
            parsed_json['fantasy_content']['teams']['0']['team'][0][2]['name']
            count = \
            parsed_json['fantasy_content']['teams']['0']['team'][1]['roster'][
                '0']['players']['count']
            players = \
            parsed_json['fantasy_content']['teams']['0']['team'][1]['roster'][
                '0']['players']

            for i in range(0, count):
                writer.writerow([players[str(i)]['player'][0][0]['player_key'],
                                 team_key])"""

    conn = sqlite3.connect(configs.db_name)
    c = conn.cursor()
    # clear out the existing data from current_rosters
    c.execute("DELETE from current_rosters")
    for team in range(1, num_teams + 1):
        url = 'http://fantasysports.yahooapis.com/fantasy/v2/teams;team_keys={league_key}.t.{team}/roster'.format(
            league_key=configs.league_key, team=str(team))
        json_string = session.get(url, params={'format': 'json'}).content
        parsed_json = json.loads(json_string.decode('utf8'))
        manager_key = parsed_json['fantasy_content']['teams']['0']['team'][0][0]['team_key']
        count = parsed_json['fantasy_content']['teams']['0']['team'][1]['roster']['0']['players']['count']
        players = parsed_json['fantasy_content']['teams']['0']['team'][1]['roster']['0']['players']
        for i in range(0, count):
            player_key = players[str(i)]['player'][0][0]['player_key']
            try:
                print("Trying to add {}, {} to table".format(player_key, manager_key))
                c.execute("INSERT OR IGNORE INTO current_rosters (player_key, manager_key) VALUES ('{}', '{}')".format(
                    player_key, manager_key))
            except sqlite3.IntegrityError:
                print('ERROR: Player Key \'{}\' already exists'.format(player_key))
    conn.commit()
    conn.close()


def get_managers(session, num_teams):
    print("Getting manager info...")
    """with open('data/managers.{league_key}.csv'.format(
            league_key=configs.league_key), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['team_key', 'team_name', 'manager'])
        # not starting with 0 in range, so need to add 1 to total teams
        for team in range(1, num_teams + 1):
            url = 'http://fantasysports.yahooapis.com/fantasy/v2/teams;team_keys={league_key}.t.{team}'.format(
                league_key=configs.league_key, team=str(team))
            json_string = session.get(url, params={'format': 'json'}).content
            parsed_json = json.loads(json_string.decode('utf8'))
            team_key = \
            parsed_json['fantasy_content']['teams']['0']['team'][0][0][
                'team_key']
            team_name = \
            parsed_json['fantasy_content']['teams']['0']['team'][0][2]['name']
            manager = \
            parsed_json['fantasy_content']['teams']['0']['team'][0][14][
                'managers'][0]['manager']['nickname']
            writer.writerow([team_key, team_name, manager])"""

    conn = sqlite3.connect(configs.db_name)
    c = conn.cursor()
    # not starting with 0 in range, so need to add 1 to total teams
    for team in range(1, num_teams + 1):
        url = 'http://fantasysports.yahooapis.com/fantasy/v2/teams;team_keys={league_key}.t.{team}'.format(
            league_key=configs.league_key, team=str(team))
        json_string = session.get(url, params={'format': 'json'}).content
        parsed_json = json.loads(json_string.decode('utf8'))
        manager_key = \
            parsed_json['fantasy_content']['teams']['0']['team'][0][0][
                'team_key']
        team_name = \
            parsed_json['fantasy_content']['teams']['0']['team'][0][2]['name']
        manager = \
            parsed_json['fantasy_content']['teams']['0']['team'][0][14][
                'managers'][0]['manager']['nickname']
        try:
            print("Trying to add {}, {}, {} to table".format(manager_key, team_name, manager))
            c.execute(
                """INSERT OR REPLACE INTO managers (manager_key,team_name, manager) VALUES ("{}", "{}", "{}")""".format(
                    manager_key, team_name, manager))
        except sqlite3.IntegrityError:
            print('ERROR: Manager Key \'{}\' already exists'.format(manager_key))
    conn.commit()
    conn.close()


def get_stats(session):
    print("Getting YTD points...")
    """with open('data/season_stats.{league_key}.csv'.format(
            league_key=configs.league_key), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['player_key', 'points'])
        rows = csv.DictReader(open(
            'data/current_rosters.{league_key}.csv'.format(
                league_key=configs.league_key)))
        for row in rows:
            player_key = row['player_key']
            url = 'http://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/players;player_keys={player_key}/stats'.format(
                league_key=configs.league_key, player_key=player_key)
            json_string = session.get(url, params={'format': 'json'}).content
            parsed_json = json.loads(json_string.decode('utf8'))
            points = \
            parsed_json['fantasy_content']['league'][1]['players']['0'][
                'player'][1]['player_points']['total']
            writer.writerow([player_key, points])"""

    conn = sqlite3.connect(configs.db_name)
    c = conn.cursor()
    c.execute("SELECT player_key FROM players")
    player_keys = []
    for row in c:
        player_keys.append(row[0])
    # not starting with 0 in range, so need to add 1 to total teams
    for player_key in player_keys:
        url = 'http://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/players;player_keys={player_key}/stats'.format(
            league_key=configs.league_key, player_key=player_key)
        json_string = session.get(url, params={'format': 'json'}).content
        parsed_json = json.loads(json_string.decode('utf8'))
        points = parsed_json['fantasy_content']['league'][1]['players']['0']['player'][1]['player_points']['total']
        try:
            print("Trying to add {}, {} to table".format(player_key, points))
            c.execute(
                """INSERT OR REPLACE INTO stats (player_key, points) VALUES ("{}", {})""".format(
                    player_key, points))
        except sqlite3.IntegrityError:
            print('ERROR: Player Key \'{}\' already exists'.format(player_key))
    conn.commit()
    conn.close()


def get_player_info(session):
    print("Getting player info...")
    """with open('data/player_info.{league_key}.csv'.format(
            league_key=configs.league_key), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(
            ['player_key', 'last_name', 'first_name', 'pos', 'team'])
        rows = csv.DictReader(open(
            'data/current_rosters.{league_key}.csv'.format(
                league_key=configs.league_key)))
        for row in rows:
            player_key = row['player_key']
            url = 'http://fantasysports.yahooapis.com/fantasy/v2/player/{player_key}'.format(
                player_key=player_key)
            json_string = session.get(url, params={'format': 'json'}).content
            parsed_json = json.loads(json_string.decode('utf8'))
            player_key = parsed_json['fantasy_content']['player'][0][0][
                'player_key']
            last_name = parsed_json['fantasy_content']['player'][0][2]['name'][
                'last']
            first_name = \
            parsed_json['fantasy_content']['player'][0][2]['name']['first']
            for i in parsed_json['fantasy_content']['player'][0]:
                if 'display_position' in i:
                    index = parsed_json['fantasy_content']['player'][0].index(
                        i)
                    pos = parsed_json['fantasy_content']['player'][0][index][
                        'display_position']
                elif 'editorial_team_abbr' in i:
                    index = parsed_json['fantasy_content']['player'][0].index(
                        i)
                    team = parsed_json['fantasy_content']['player'][0][index][
                        'editorial_team_abbr']
            writer.writerow([player_key, last_name, first_name, pos, team])"""

    conn = sqlite3.connect(configs.db_name)
    c = conn.cursor()
    c.execute("SELECT player_key FROM current_rosters")
    player_keys = []
    for row in c:
        player_keys.append(row[0])
    for player_key in player_keys:
        url = 'http://fantasysports.yahooapis.com/fantasy/v2/player/{player_key}'.format(
            player_key=player_key)
        json_string = session.get(url, params={'format': 'json'}).content
        parsed_json = json.loads(json_string.decode('utf8'))
        last_name = parsed_json['fantasy_content']['player'][0][2]['name'][
            'last']
        first_name = parsed_json['fantasy_content']['player'][0][2]['name']['first']
        for i in parsed_json['fantasy_content']['player'][0]:
            if 'display_position' in i:
                index = parsed_json['fantasy_content']['player'][0].index(i)
                pos = parsed_json['fantasy_content']['player'][0][index]['display_position']
            elif 'editorial_team_abbr' in i:
                index = parsed_json['fantasy_content']['player'][0].index(i)
                nfl_team = parsed_json['fantasy_content']['player'][0][index]['editorial_team_abbr']
        try:
            print(
                "Trying to add {}, {}, {}, {}, {} to table".format(player_key,
                                                                   last_name,
                                                                   first_name,
                                                                   pos,
                                                                   nfl_team))
            c.execute(
                """INSERT OR REPLACE INTO players (player_key, last_name, first_name, position, nfl_team) VALUES ("{}", "{}","{}","{}", "{}")""".format(
                    player_key, last_name, first_name, pos, nfl_team))
        except sqlite3.IntegrityError:
            print('ERROR: Player Key \'{}\' already exists'.format(player_key))

    conn.commit()
    conn.close()


num_teams, positions, num_roster_spots = get_league_info(session)
get_managers(session, num_teams)

# only run this if auction_values.csv doesn't exist
get_auction_values(session) #GOOD

get_current_rosters(session, num_teams) #GOOD
get_player_info(session)
get_stats(session)
