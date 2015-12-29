__author__ = 'Alex Hart'

import create_league_db
import download_data
import compile_data

# create the new DB
create_league_db.create_db()

# create a yahoo api session
session = download_data.login()

# set some league variables needed for other downloads
num_teams, positions, num_roster_spots = download_data.get_league_info(session)

# download data
download_data.get_managers(session, num_teams)
download_data.get_auction_values(session)
download_data.get_current_rosters(session, num_teams)
download_data.get_player_info(session)
download_data.get_stats(session)

# update tables from other information
download_data.dump_rookie_info()
download_data.dump_undrafted_players()

# compile data
compile_data.compile_future_salaries()