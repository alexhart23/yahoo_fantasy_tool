__author__ = 'Alex Hart'

import csv
import configs
import math
import pandas as pd
import glob
import sqlite3


def compile_future_salaries():
    """with open('data/Future_Keeper_Values.{league_key}.csv'.format(league_key=configs.league_key),'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        years = calculate_years_range()
        header = ['player_key'] + years
        writer.writerow(header)
        rows = csv.DictReader(open('data/auction_values.{league_key}.csv'.format(league_key=configs.league_key)))
        for row in rows:
            player_key = row['player_key']
            starting_cost = row['cost']
            salaries = calculate_future_salaries(player_key,starting_cost)
            writer.writerow([player_key]+salaries)"""

    #years = calculate_years_range()
    conn = sqlite3.connect(configs.db_name)
    c = conn.cursor()
    c.execute("SELECT player_key,\"{}_cost\" FROM auction_values".format(configs.year))
    keys = []
    for row in c:
        keys.append([row[0],row[1]])
    for player_key,cost in keys:
        starting_cost = cost
        print(player_key, starting_cost)
        salaries = calculate_future_salaries(player_key, starting_cost)
        try:
            print("Trying to add {}, {}, {}, {}, {}, {} to table".format(player_key, salaries[0], salaries[1], salaries[2], salaries[3], salaries[4]))
            c.execute(
                """INSERT OR REPLACE INTO auction_values (player_key, '{}_cost', '{}_cost', '{}_cost', '{}_cost', '{}_cost') VALUES ("{}", {}, {}, {}, {}, {})""".format(
                    configs.year, configs.year+1, configs.year+2, configs.year+3, configs.year+4,
                    player_key, salaries[0], salaries[1], salaries[2], salaries[3], salaries[4]))
        except sqlite3.IntegrityError:
            print('ERROR: Player Key \'{}\' already exists'.format(player_key))

    conn.commit()
    conn.close()


def calculate_years_range(current_year=configs.year):
    years = [current_year]
    while len(years) < configs.years_in_future:
        years.append(years[-1]+1)
    return years


def calculate_future_salaries(player_key, current_cost=1, current_year=configs.year):
    cost = int(current_cost)
    #rows = csv.DictReader(open('data/rookies.{league_key}.csv'.format(league_key=configs.league_key)))
    conn = sqlite3.connect(configs.db_name)
    c = conn.cursor()
    #c.execute("SELECT player_key,cost,year FROM rookies") #TODO change this to year_drafted
    #if c.execute("SELECT EXISTS(SELECT player_key FROM rookies WHERE player_key ='{}' LIMIT 1)".format(player_key)):
    #    for row in c:
    #        print(row)
    c.execute("SELECT player_key,cost,year FROM rookies WHERE player_key ='{}' LIMIT 1".format(player_key))
    keys = []
    for row in c:
        keys.append([row[0],row[1],row[2]])
    if keys == []:
        salaries = [current_cost]
        while len(salaries) < configs.years_in_future:
            if math.ceil(cost * .2) <= 5:
                cost = int(salaries[-1]) + 5
            else:
                cost = math.ceil(int(salaries[-1]) * 1.2)
            salaries.append(cost)
        return salaries
    else:
        for rookie, cost, year in keys:
            print('see if %s matches %s' % (player_key, rookie))
            if player_key == rookie:
                print('found a match!')
                salaries = [current_cost]
                drafted_year = year
                # rookie contracts last 4 years. first cost is already added, so skip one
                remaining_years = (drafted_year + 3) - current_year
                for x in range(remaining_years):
                    salaries.append(cost)
                # TODO figure out expected franchise cost
                # hard coding $32 for now
                salaries.append(32)
                while len(salaries) < configs.years_in_future:
                    cost = math.ceil(int(salaries[-1]) * 1.2)
                    salaries.append(cost)
                return salaries
                break

if __name__ == "__main__":
    compile_future_salaries()






