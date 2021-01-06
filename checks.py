#### This file contains checking helper functions. They return either a message or False ####
from flask import  session
import json, re
import hashing
from app import db
from models import Player, PastGame, Game

### verifier that checks that a username and password is good to log in with. Makes sure they're non-empty and are in the database ###
## returns an error message if there is an error. False if there is no error ##
def check_for_login_error(user, password):
    if len(user) == 0:
        return "You must have a username"
    if len(password) == 0:
        return "You must have a password."

    foundUser = Player.query.filter_by(user=user).first()
    if not foundUser:
        return "No such user exists"
    if not hashing.verify(password, foundUser.password):
        return "username or password is wrong."
    return  False
        
### verifier that checks that a username, password and name are good to sign up with. makes sure it's long and is in the database ###
## returns an error message if there is an error. False if there is no error ##
def check_for_signup_error(user, password, passwordRepeat, name):
    if len(user) < 5:
        return "username must be at least 5 letters!"
    if len(user) > 20:
        return "username can't be more than 20 letters! Sorry if you wanted 'dontsaypineapplegod01' as your username."
    if not user.isalnum():
        return "username can only contain letters and numbers!"
    if len(password) < 5:
        return "password must be at least 5 characters!"
    if len(password) > 100:
        return "password can't be more than 100 characters! It's not THAT important that no one can play DSP for you."
    if re.search("[\s]", password):
        return "password can't contain whitespaces!"
    if password == user:
        return "username and password must be different!"
    if password != passwordRepeat:
        return "The passwords must match."
    if len(name) == 0:
        return "You must have a name!"
    if len(name) < 2:
        return "Name must be at least 2 characters!"
    if len(user) > 20:
        return "Name can't be more than 20 characters! And if yours is, think of a nickname."
    if Player.query.filter_by(user=user).first():
        return "Oh no! Someone already took this username."
    return  False


def check_for_rename_error(name, status):
    if len(name) == 0:
        return "You must have a name!"
    if len(name) < 2:
        return "Name must be at least 2 characters!"
    if len(name) > 20:
        return "Name can't be more than 20 characters! And if yours is, think of a nickname."
    if len(status) > 40:
        return "Status can't be more than 40 characters! There's no way you have that many thoughts."

### checks that given settings are good ###
def check_for_settings_error(settings):
    try:
        if settings['difficulty'] not in ['easy', 'medium', 'hard']:
            return "settings difficulty error"
        if settings['passon'] not in ['pass', 'shuffle']:
            return "settings passon error"
        return False
    except KeyError:
        return False

### verifier that checks that a code is good to join with. makes sure it's an actual game and that the user is not already in the game ###
## returns an error message if there is an error. False if there is no error ##
def check_for_join_error(code):
    if not code:
        return "please enter a game code"
    foundGame = Game.query.filter_by(code = code).first()
    if not foundGame:
        return "no such game exists"
    if foundGame.started:
        return "This game has already started."
    if session['user'] in json.loads(foundGame.players):
        return "You are already in this game."
    return False

### verifier that checks that a code and name are good to c with. makes sure code is long enough, name is non empty, and that the game doesnt already exist ###
## returns an error message if there is an error. False if there is no error ##
def check_for_create_error(code, name, settings):
    error = check_for_settings_error(settings)
    if error:
        return error
    if len(code)<5:
        return "Code must be at least 5 letters."
    if len(code)>10:
        return "Code can't be more than 10 letters. This isnt a nuclear launch you're organizing."
    if not code.isalnum():
        return "Code can only contain letters and numbers!"
    if len(name)==0:
        return "Your game must have a name."
    if len(name) > 20:
        return "The name can't be more than 20 letters. Try something simpler :)"
    if Game.query.filter_by(code = code).first():
        return "A game with this code already exists"
    if PastGame.query.filter_by(code = code).first():
        return "A game with this code already exists"
    return False

def check_for_cancel_error(code):
    foundGame = Game.query.filter_by(code = code).first()
    if not foundGame:
        return "Game has already ended or does not exist."
    if foundGame.started:
        return "This game has already started."
    return False

def check_for_start_error(code):
    foundGame = Game.query.filter_by(code = code).first()
    if not foundGame:
        return "Game has already ended or does not exist."
    if foundGame.started:
        return "This game has already started."
    if len(json.loads(foundGame.players)) < 2:
        return "You need at least 2 players to play!"
    return False

### verifies that a kick is valid ###
def check_for_kick_error(code, user):
    foundGame = Game.query.filter_by(code = code).first()
    if not foundGame:
        return "Game has already ended or does not exist."
    if foundGame.started:
        return "This game has already started."
    if user not in json.loads(foundGame.players):
        return "This user is not in the game"
    if user == foundGame.host:
        return "You can't kick yourself. Think about the game you're leaving with no supervisor o.o"
    return False

### verifies that a kill is valid ###
def check_for_killed_error(code, user):
    foundGame = Game.query.filter_by(code = code).first()
    if not foundGame:
        return "Game has already ended or does not exist."
    if user not in json.loads(foundGame.alive):
        return "You are already dead!"
    return False

### verifies that a purge is valid ###
def check_for_purge_error(code, user):
    foundGame = Game.query.filter_by(code = code).first()
    if not foundGame:
        return "Game has already ended or does not exist."
    if user not in json.loads(foundGame.alive):
        return "You are already dead!"
    return False

### verifies that a user is an actual player in the game ###
def check_if_game_complete(code):
    if Game.query.filter_by(code = code).first():
        return "active"
    if PastGame.query.filter_by(code = code).first():
        return "past"
    return False
