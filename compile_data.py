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

    for i in ['season_stats','auction_values','current_rosters','managers']:
        new = pd.read_csv(glob.glob("data/{file}*.csv".format(file=i))[0])
        all_data = pd.merge(all_data, new, how='left')

    all_data.to_csv(path_or_buf='data/Full_Data.{league_key}.csv'.format(league_key=configs.league_key))

combine_data()


def compile_future_salaries():
    with open('data/Full_Auction_Values.{league_key}.csv'.format(league_key=configs.league_key),'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['player_key','name','pos','team',str(configs.year),str(configs.year+1),str(configs.year+2),str(configs.year+3),str(configs.year+4)])
        rows = csv.DictReader(open('data/current_rosters.{league_key}.csv'.format(league_key=configs.league_key)))
        for row in rows:
            player_key = row['player_key']





