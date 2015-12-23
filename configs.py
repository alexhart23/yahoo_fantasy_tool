__author__ = 'Alex Hart'

season_id = '348' # 348 for 2015 NFL
league_id = 'your league id' # check the url on your league page
year = 2015
league_key = season_id+".l."+league_id
db_name = league_key+'_fantasy_data.db'

# how many years we want to calculate keep values for
years_in_future = 5

OAUTH_CONSUMER_KEY = 'your key'
OAUTH_SHARED_SECRET = 'your secret'