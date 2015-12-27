from flask import g, render_template, request
from app import app
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
    cur = g.db.execute('SELECT last_name,first_name,position,nfl_team,IFNULL("{}_cost",1) as cost '
                       'FROM players LEFT OUTER JOIN auction_values '
                       'ON players.player_key = auction_values.player_key'.format(configs.year))
    players = sorted([dict(last_name=row['last_name'],
                    first_name=row['first_name'],
                    position=row['position'],
                    team=row['nfl_team'],
                    cost=row['cost']) for row in cur.fetchall()],
                     key=lambda k: k['last_name'])
    return render_template('players.html', players=players, year=configs.year)

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
    cur = g.db.execute('SELECT last_name,first_name,position,nfl_team,IFNULL("{}_cost",1) as cost '
                       'FROM players LEFT OUTER JOIN auction_values '
                       'ON players.player_key = auction_values.player_key '
                       'WHERE manager_key="{}"'.format(configs.year,manager_key))
    players = sorted([dict(last_name=row['last_name'],
                    first_name=row['first_name'],
                    position=row['position'],
                    team=row['nfl_team'],
                    cost=row['cost']) for row in cur.fetchall()],
                     key=lambda k: k['last_name'])
    return render_template('rosters.html', managers=managers, players=players)
