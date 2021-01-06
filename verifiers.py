#### This file contains verifier helper functions. They all return a boolean value ####
from flask import  session
import json
import hashing
from app import db
from models import Player, PastGame, Game

### verfier that a user is logged in on a page ###
def verify_session_logged_in():
    if not (session.get('loggedIn') and session.get('user') and session.get('password')): #checks that loggedIn and user session variables exist
        return False
    foundPlayer = Player.query.filter_by(user = session['user']).first()
    if not foundPlayer: #checks that user exists 
        return false
    if not hashing.verify(session['password'], foundPlayer.password): # checks that passwords match
        return False
    return session['loggedIn'] #makes sure logged in variable is set to true

### verifies that a user is an actual player in the (active) game ###
def verify_user_in_game(user, code):
    foundGame = Game.query.filter_by(code = code)
    if not foundGame:
        return False
    return user in json.loads(foundGame.players)

## verifies that the session user is the host ##
def verify_host(code):
    user = session['user']
    foundGame = Game.query.filter_by(code = code)
    if not foundGame:
        return False
    return user == foundGame.host
