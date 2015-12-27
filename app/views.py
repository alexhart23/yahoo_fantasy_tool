from flask import g, render_template, request
from app import app
import compile_data
import configs
import sqlite3


@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")


@app.before_request
def before_request():
    g.db = sqlite3.connect(configs.db_name)
    g.db.row_factory = sqlite3.Row

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


@app.route('/players')
def players():
    cur = g.db.execute('SELECT * '
                       'FROM players LEFT OUTER JOIN auction_values '
                       'ON players.player_key = auction_values.player_key '
                       'LEFT OUTER JOIN managers '
                       'ON players.manager_key = managers.manager_key ')
    players = sorted([dict(last_name=row['last_name'],
                    first_name=row['first_name'],
                    position=row['position'],
                    team=row['nfl_team'],
                    cost1=row['{}_cost'.format(str(configs.year))],    # year1
                    cost2=row['{}_cost'.format(str(configs.year+1))],  # year2
                    cost3=row['{}_cost'.format(str(configs.year+2))],  # year3
                    cost4=row['{}_cost'.format(str(configs.year+3))],  # year4
                    cost5=row['{}_cost'.format(str(configs.year+4))],  # year5
                    owner=row['manager']) for row in cur.fetchall()],
                     key=lambda k: k['last_name'])
    years = compile_data.calculate_years_range()
    return render_template('players.html', players=players, years=years)

@app.route('/rosters', methods=['GET', 'POST'])
def rosters():
    cur = g.db.execute('SELECT manager_key,manager FROM managers')
    managers = sorted([dict(manager_key=row['manager_key'],
                    manager=row['manager']) for row in cur.fetchall()],
                     key=lambda k: k['manager'])
    try:
        manager_key = request.form["managers"]
    except:
        manager_key = managers[0]['manager_key']
    cur = g.db.execute('SELECT * '
                       'FROM players LEFT OUTER JOIN auction_values '
                       'ON players.player_key = auction_values.player_key '
                       'LEFT OUTER JOIN managers '
                       'ON players.manager_key = managers.manager_key '
                       'WHERE managers.manager_key="{}"'.format(manager_key))
    players = sorted([dict(last_name=row['last_name'],
                    first_name=row['first_name'],
                    position=row['position'],
                    team=row['nfl_team'],
                    cost1=row['{}_cost'.format(str(configs.year))],    # year1
                    cost2=row['{}_cost'.format(str(configs.year+1))],  # year2
                    cost3=row['{}_cost'.format(str(configs.year+2))],  # year3
                    cost4=row['{}_cost'.format(str(configs.year+3))],  # year4
                    cost5=row['{}_cost'.format(str(configs.year+4))],  # year5
                    owner=row['manager']) for row in cur.fetchall()],
                     key=lambda k: k['last_name'])
    years = compile_data.calculate_years_range()
    return render_template('rosters.html', managers=managers, players=players, years=years)
