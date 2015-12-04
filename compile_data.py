__author__ = 'Alex Hart'

import csv
import configs
import math
import pandas as pd
import glob


def combine_data():
    all_data = pd.DataFrame()
    for f in glob.glob("data/player_info*.csv"):
        df = pd.read_csv(f)
        all_data = all_data.append(df,ignore_index=True)

    for i in ['season_stats','Future_Keeper_Values','current_rosters','managers']:
        new = pd.read_csv(glob.glob("data/{file}*.csv".format(file=i))[0])
        all_data = pd.merge(all_data, new, how='left')

    all_data.to_csv(path_or_buf='data/Full_Data.{league_key}.csv'.format(league_key=configs.league_key))

#combine_data()


def compile_future_salaries():
    with open('data/Future_Keeper_Values.{league_key}.csv'.format(league_key=configs.league_key),'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        years = calculate_years_range()
        header = ['player_key'] + years
        writer.writerow(header)
        rows = csv.DictReader(open('data/auction_values.{league_key}.csv'.format(league_key=configs.league_key)))
        for row in rows:
            player_key = row['player_key']
            starting_cost = row['cost']
            salaries = calculate_future_salaries(player_key,starting_cost)
            writer.writerow([player_key]+salaries)

def calculate_years_range(current_year=configs.year):
    years = [current_year]
    while len(years) < configs.years_in_future:
        years.append(years[-1]+1)
    return years


def calculate_future_salaries(player_key, current_cost=1, current_year=configs.year):
    cost = int(current_cost)
    rows = csv.DictReader(open('data/rookies.{league_key}.csv'.format(league_key=configs.league_key)))
    for row in rows:
        if player_key == row['player_key']:
            salaries = [current_cost]
            cost = int(row['cost'])
            drafted_year = int(row['year_drafted'])
            # rookie contracts last 4 years. first cost is already added, so skip one
            remaining_years = (drafted_year+3)-current_year
            for x in range(remaining_years):
                salaries.append(cost)
            # TODO figure out expected franchise cost
            # hard coding $32 for now
            salaries.append(32)
            while len(salaries) < configs.years_in_future:
                cost = math.ceil(int(salaries[-1]) * 1.2)
                salaries.append(cost)
            break
        else:
            salaries = [current_cost]
            while len(salaries) < configs.years_in_future:
                if math.ceil(cost * .2) <= 5:
                    cost = int(salaries[-1]) + 5
                else:
                    cost = math.ceil(int(salaries[-1]) * 1.2)
                salaries.append(cost)
            break
    return salaries

compile_future_salaries()
combine_data()






