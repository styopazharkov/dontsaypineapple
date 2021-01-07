#### This file contains helper functions that fetch information and modify the database####
from flask import  session
import json
from app import db
from models import Player, PastGame, Game


def get_active_button_info(code):
    foundGame = Game.query.filter_by(code = code).first()
    return {
        'name': foundGame.name,
        'code': code,
        'numberOfPlayers': len(json.loads(foundGame.players)), 
        'numberOfAlive': len(json.loads(foundGame.alive)), 
        'started': foundGame.started, 
        'host': foundGame.host
        }

def get_past_button_info(code):
    foundGame = PastGame.query.filter_by(code = code).first()
    return {
        'name': foundGame.name, 
        'code': code, 
        'numberOfPlayers': len(json.loads(foundGame.players)), 
        'host': foundGame.host, 
        'killWinners': foundGame.killWinners, 
        'survivalWinner': foundGame.survivalWinner
        }

#distributes kills (actually modifies the database)
def distribute_kills_and_wins(players, killCount, survivalWinner, killWinners):
    for player in players:
        foundPlayer = Player.query.filter_by(user = player).first()
        stats = json.loads(foundPlayer.stats)
        stats["played"] += 1
        stats["kills"] += killCount[player]
        stats["survivalWins"] += int(player == survivalWinner)
        stats["killWins"] += (int(player in killWinners)/len(killWinners))
        foundPlayer.stats = json.dumps(stats)
        db.session.commit()

### gets the name of a user from username ###
def get_name(user):
    return Player.query.filter_by(user=user).first().name

### gets the status of a user from username ###
def get_status(user):
    return Player.query.filter_by(user=user).first().status

def get_theme(user):
    return Player.query.filter_by(user=user).first().theme