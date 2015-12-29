__author__ = 'Alex Hart'

import sqlite3
import configs
import os
import sys


def calculate_years_range(current_year=configs.year):
    years = [current_year]
    while len(years) < configs.years_in_future:
        years.append(years[-1] + 1)
    return years

def create_db():
    if os.path.isfile(configs.db_name):
        print("{} already exists. Exiting...".format(configs.db_name))
        sys.exit(1)



    conn = sqlite3.connect(configs.db_name)

    c = conn.cursor()

    c.execute("""CREATE table league (
             league_key text primary key not NULL UNIQUE,
             num_teams int,
             num_roster_spots int)""")

    c.execute("""CREATE table managers (
             manager_key text primary key not NULL UNIQUE,
             team_name text,
             manager text)""")

    c.execute("""CREATE table players (
             player_key text primary key not NULL UNIQUE,
             last_name text,
             first_name text,
             position text,
             nfl_team text,
             manager_key text REFERENCES managers(manager_key))""")

    c.execute("""CREATE table auction_values (
             player_key text REFERENCES players(player_key) UNIQUE)""")

    years = calculate_years_range()
    for year in years:
        c.execute("""ALTER TABLE auction_values ADD COLUMN '{}_cost'""".format(year))

    c.execute("""CREATE table stats (
             player_key text REFERENCES players(player_key) UNIQUE,
             points float)""")

    c.execute("""CREATE table current_rosters (
             player_key text REFERENCES players(player_key) UNIQUE,
             manager_key text REFERENCES managers(manager_key))""")

    c.execute("""CREATE table rookies (
             player_key text REFERENCES players(player_key) UNIQUE,
             cost int,
             year int)""")

    conn.commit()
    conn.close()
