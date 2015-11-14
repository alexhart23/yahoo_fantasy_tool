__author__ = 'Alex Hart'

from rauth import OAuth1Service
import json
import csv
import configs

def login():
    request_token_url = 'https://api.login.yahoo.com/oauth/v2/get_request_token'
    authorize_url = 'https://api.login.yahoo.com/oauth/v2/request_auth'
    access_token_url = 'https://api.login.yahoo.com/oauth/v2/get_token'

    yahoo = OAuth1Service(consumer_key=configs.OAUTH_CONSUMER_KEY,\
                          consumer_secret=configs.OAUTH_SHARED_SECRET,\
                          name='yahoo',\
                          access_token_url=access_token_url,\
                          authorize_url=authorize_url,\
                          request_token_url=request_token_url,\
                          base_url='https://api.login.yahoo.com/oauth/v2/')

    request_token, request_token_secret = yahoo.get_request_token\
    (data = {'oauth_callback': 'http://127.0.0.1/' })

    print("Request Token:")
    print (" - oauth_token = %s" % request_token)
    print (" - oauth_token_secret = %s" % request_token_secret)
    auth_url = yahoo.get_authorize_url(request_token)
    print ('Visit this URL in your browser: ' + auth_url)

    pin = input('Enter PIN from browser: ')

    session = yahoo.get_auth_session(request_token,\
                                     request_token_secret,\
                                     method='POST',\
                                     data={'oauth_verifier': pin})
    return session

session = login()

# age

# ROS projected points

def get_league_info(session):
    print("Getting league info...")
    url = 'http://fantasysports.yahooapis.com/fantasy/v2/leagues;league_keys={league_key}/settings'.format(league_key=configs.league_key)
    json_string = session.get(url, params={'format': 'json'}).content
    parsed_json = json.loads(json_string.decode('utf8'))
    num_teams = parsed_json['fantasy_content']['leagues']['0']['league'][0]['num_teams']

    # get starting positions
    positions = {}
    #print(parsed_json['fantasy_content']['leagues']['0']['league'][1]['settings'][0]['roster_positions'][1]['roster_position']['position'])
    for i in parsed_json['fantasy_content']['leagues']['0']['league'][1]['settings'][0]['roster_positions']:
        positions[i['roster_position']['position']] = i['roster_position']['count']

    num_roster_spots = sum([i for i in positions.values() if type(i) != str])

    return num_teams, positions, num_roster_spots


# this only needs to be run once after the draft
def get_auction_values(session):
    print("Getting auction values...")
    url = 'http://fantasysports.yahooapis.com/fantasy/v2/leagues;league_keys={league_key}/draftresults'.format(league_key=configs.league_key)
    json_string = session.get(url, params={'format': 'json'}).content
    parsed_json = json.loads(json_string.decode('utf8'))
    #print(parsed_json['fantasy_content']['leagues']['0']['league'][1]['draft_results']['170']['draft_result']['player_key'])
    num_drafted = parsed_json['fantasy_content']['leagues']['0']['league'][1]['draft_results']['count']

    with open('auction_values.{league_key}.csv'.format(league_key=configs.league_key),'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['player_key','cost'])
        for i in range(0,num_drafted):
            writer.writerow([parsed_json['fantasy_content']['leagues']['0']['league'][1]['draft_results'][str(i)]['draft_result']['player_key'],
                            parsed_json['fantasy_content']['leagues']['0']['league'][1]['draft_results'][str(i)]['draft_result']['cost']])


def get_current_rosters(session, num_teams):
    print("Getting current rosters...")
    with open('current_rosters.{league_key}.csv'.format(league_key=configs.league_key),'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['player_key','team_key'])
        # not starting with 0 in range, so need to add 1 to total teams
        for team in range(1,num_teams+1):
            url = 'http://fantasysports.yahooapis.com/fantasy/v2/teams;team_keys={league_key}.t.{team}/roster'.format(league_key=configs.league_key,team=str(team))
            json_string = session.get(url, params={'format': 'json'}).content
            parsed_json = json.loads(json_string.decode('utf8'))
            # need team_key, player_key, first, last, editorial_team_abbr, display_position, eligible_positions
            team_key = parsed_json['fantasy_content']['teams']['0']['team'][0][0]['team_key']
            team_name = parsed_json['fantasy_content']['teams']['0']['team'][0][2]['name']
            count = parsed_json['fantasy_content']['teams']['0']['team'][1]['roster']['0']['players']['count']
            players = parsed_json['fantasy_content']['teams']['0']['team'][1]['roster']['0']['players']

            for i in range(0, count):
                writer.writerow([players[str(i)]['player'][0][0]['player_key'],
                                team_key])

def get_managers(session, num_teams):
    print("Getting manager info...")
    with open('managers.{league_key}.csv'.format(league_key=configs.league_key),'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['team_key','team_name','manager'])
        # not starting with 0 in range, so need to add 1 to total teams
        for team in range(1,num_teams+1):
            url = 'http://fantasysports.yahooapis.com/fantasy/v2/teams;team_keys={league_key}.t.{team}'.format(league_key=configs.league_key,team=str(team))
            json_string = session.get(url, params={'format': 'json'}).content
            parsed_json = json.loads(json_string.decode('utf8'))
            team_key = parsed_json['fantasy_content']['teams']['0']['team'][0][0]['team_key']
            team_name = parsed_json['fantasy_content']['teams']['0']['team'][0][2]['name']
            manager = parsed_json['fantasy_content']['teams']['0']['team'][0][14]['managers'][0]['manager']['nickname']
            writer.writerow([team_key,team_name,manager])

def get_stats(session):
    print("Getting YTD points...")
    with open('season_stats.{league_key}.csv'.format(league_key=configs.league_key),'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['player_key','points'])
        rows = csv.DictReader(open('current_rosters.{league_key}.csv'.format(league_key=configs.league_key)))
        for row in rows:
            player_key = row['player_key']
            url = 'http://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/players;player_keys={player_key}/stats'.format(league_key=configs.league_key,player_key=player_key)
            json_string = session.get(url, params={'format': 'json'}).content
            parsed_json = json.loads(json_string.decode('utf8'))
            points = parsed_json['fantasy_content']['league'][1]['players']['0']['player'][1]['player_points']['total']
            writer.writerow([player_key,points])

def get_player_info(session):
    print("Getting player info...")
    with open('player_info.{league_key}.csv'.format(league_key=configs.league_key),'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['player_key','last_name','first_name','pos','team'])
        rows = csv.DictReader(open('current_rosters.{league_key}.csv'.format(league_key=configs.league_key)))
        for row in rows:
            player_key = row['player_key']
            url = 'http://fantasysports.yahooapis.com/fantasy/v2/player/{player_key}'.format(player_key=player_key)
            json_string = session.get(url, params={'format': 'json'}).content
            parsed_json = json.loads(json_string.decode('utf8'))
            player_key = parsed_json['fantasy_content']['player'][0][0]['player_key']
            last_name = parsed_json['fantasy_content']['player'][0][2]['name']['last']
            first_name = parsed_json['fantasy_content']['player'][0][2]['name']['first']
            for i in parsed_json['fantasy_content']['player'][0]:
                if 'display_position' in i:
                    index = parsed_json['fantasy_content']['player'][0].index(i)
                    pos = parsed_json['fantasy_content']['player'][0][index]['display_position']
                elif 'editorial_team_abbr' in i:
                    index = parsed_json['fantasy_content']['player'][0].index(i)
                    team = parsed_json['fantasy_content']['player'][0][index]['editorial_team_abbr']
            writer.writerow([player_key,last_name,first_name,pos,team])

num_teams, positions, num_roster_spots = get_league_info(session)
get_managers(session,num_teams)

# only run this if auction_values.csv doesn't exist
get_auction_values(session)

get_current_rosters(session,num_teams)
get_player_info(session)
get_stats(session)









