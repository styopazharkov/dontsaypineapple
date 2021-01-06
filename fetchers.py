#### This file contains helper functions that fetch information and modify the database####
from flask import  session
import json
from app import db
from models import Player, PastGame, Game


def get_active_button_info(game):
    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row  
        cur = con.cursor()  
        row = cur.execute("SELECT * from Games WHERE code = ?", (game, )) .fetchone()
    return {'name': row['name'], 'code': game, 'numberOfPlayers': len(json.loads(row['players'])), 'numberOfAlive': len(json.loads(row['alive'])), 'started': row['started'], 'host': row['host']}

def get_past_button_info(game):
    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row  
        cur = con.cursor()  
        row = cur.execute("SELECT * from pastGames WHERE code = ?", (game, )) .fetchone()
    return {'name': row['name'], 'code': game, 'numberOfPlayers': len(json.loads(row['players'])), 'host': row['host'], 'killWinners': row['killWinners'], 'survivalWinner': row['survivalWinner']}

def distribute_kills_and_wins(cur, players, killCount, survivalWinner, killWinners):
    for player in players:
        stats = json.loads(cur.execute("SELECT * from Players WHERE user = ? ", (player, )).fetchone()["stats"])
        stats["played"] += 1
        stats["kills"] += killCount[player]
        stats["survivalWins"] += int(player == survivalWinner)
        stats["killWins"] += (int(player in killWinners)/len(killWinners))
        stats=json.dumps(stats)
        cur.execute("UPDATE Players SET stats = ? WHERE user = ? ", (stats, player))

### gets the name of a user from username ###
def get_name(cur, user):
    return cur.execute("SELECT * from Players WHERE user = ?", (user, )).fetchone()['name']

### gets the status of a user from username ###
def get_status(cur, user):
    return cur.execute("SELECT * from Players WHERE user = ?", (user, )).fetchone()['status']

def get_theme(cur, user):
    return cur.execute("SELECT * from Players WHERE user = ?", (user, )).fetchone()['theme']