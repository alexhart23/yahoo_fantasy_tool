from flask import g, render_template
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
    cur = g.db.execute('SELECT last_name,first_name,position,nfl_team,IFNULL(cost,1) as cost '
                       'FROM players LEFT OUTER JOIN auction_values '
                       'ON players.player_key = auction_values.player_key')
    players = sorted([dict(last_name=row['last_name'],
                    first_name=row['first_name'],
                    position=row['position'],
                    team=row['nfl_team'],
                    cost=row['cost']) for row in cur.fetchall()],
                     key=lambda k: k['last_name'])
    return render_template('player_table.html', players=players, year=configs.year)
