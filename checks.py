#### This file contains checking helper functions. They return either a message or False ####
from flask import  session
import sqlite3, json
import hashing
import re

### verifier that checks that a username and password is good to log in with. Makes sure they're non-empty and are in the database ###
## returns an error message if there is an error. False if there is no error ##
def check_for_login_error(user, password):
    if len(user) == 0:
        return "You must have a username"
    if len(password) == 0:
        return "You must have a password."
    with sqlite3.connect("database.db") as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        if cur.execute("SELECT count(*) FROM Players WHERE user= ? ", (user, )).fetchone()[0] == 0: #checks that username exsts
            return "No such user exists"
        if not hashing.verify(password, cur.execute("SELECT * FROM Players WHERE user = ? ", (session['user'], )).fetchone()['password']): # checks that passwords match
            return "The username or password is wrong"
    return  False
        
### verifier that checks that a username, password and name are good to sign up with. makes sure it's long and is in the database ###
## returns an error message if there is an error. False if there is no error ##
def check_for_signup_error(user, password, passwordRepeat, name):
    #TODO: check that the username only contains normal characters
    if len(user) < 5:
        return "Your username can't be less than 5 characters long."
    if len(user) > 20:
        return "Your username can't be more than 20 characters long."
    if re.search("[\s]", user):
        return "Your username can't contain spaces or other whitespace characters"
    if len(password) < 5:
        return "Your password can't be less than 5 characters long."
    if len(password) > 100:
        return "Your password can't be more than 100 characters long."
    if re.search("[\s]", password):
        return "Your password can't contain spaces or other whitespace characters"
    if password == user:
        return "Your username and password must be different!"
    if password != passwordRepeat:
        return "The passwords must match."
    if len(name.strip()) == 0:
        return "You must have a name!"
    with sqlite3.connect("database.db") as con:
        cur = con.cursor()
        if cur.execute("SELECT count(*) FROM Players WHERE user= ? ", (user, )).fetchone()[0] > 0:
            return "Oh no! Someone already took this username."
    return  False

def check_for_rename_error(name, status):
    #TODO: more checks here
    if len(name.strip()) == 0:
        return "You must have a name!"

def check_for_settings_error(settings):
    try:
        if settings['difficulty'] not in ['debug', 'easy', 'medium', 'hard']:
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
    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row
        cur = con.cursor() 
        if cur.execute("SELECT count(*) FROM Games WHERE code = ? ", (code, )).fetchone()[0] == 0:
            return "no such game exists" 
        row =  cur.execute("SELECT * FROM Games WHERE code = ? ", (code, )).fetchone()
        if row['started']:
            return "this game has already started"
        if session['user'] in row['players']:
            return "you are already in this game"
    return False

### verifier that checks that a code and name are good to c with. makes sure code is long enough, name is non empty, and that the game doesnt already exist ###
## returns an error message if there is an error. False if there is no error ##
def check_for_create_error(code, name, settings):
    #TODO: check for valid settings
    if len(code)<5:
        return "game code must be at least 5 characters long"
    if len(name.strip())==0:
        return "your game must have a name"
    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row
        cur = con.cursor() 
        if cur.execute("SELECT count(*) FROM Games WHERE code = ? ", (code, )).fetchone()[0] > 0:
            return "A game with this code already exists"
        if cur.execute("SELECT count(*) FROM PastGames WHERE code = ? ", (code, )).fetchone()[0] > 0:
            return "A game with this code already exists"
    return False

def check_for_cancel_error(code):
    with sqlite3.connect("database.db") as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        if cur.execute("SELECT count(*) FROM Games WHERE code = ? ", (code, )).fetchone()[0] == 0:
            return "This game has already ended or does not exist"
        if cur.execute("SELECT * FROM Games WHERE code= ? ", (code, )).fetchone()["started"]:
            return "This game has already started"
    return False

def check_for_start_error(code):
    with sqlite3.connect("database.db") as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        if len(json.loads(cur.execute("SELECT * FROM Games WHERE code= ? ", (code, )).fetchone()["players"])) < 2:
            return "You need at least 2 players to play!"
    return False

### verifies that a cancel is valid ###
def check_for_kick_error(code):
    with sqlite3.connect("database.db") as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        if cur.execute("SELECT count(*) FROM Games WHERE code = ? ", (code, )).fetchone()[0] == 0:
            return "This game has already ended or does not exist"
    return False

### verifies that a kick is valid ###
def check_for_kick_error(code, user):
    with sqlite3.connect("database.db") as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        if cur.execute("SELECT count(*) FROM Games WHERE code = ? ", (code, )).fetchone()[0] == 0:
            return "This game has already ended."
        row = cur.execute("SELECT * FROM Games WHERE code= ? ", (code, )).fetchone()
        if row['started']:
            return "This game has already started"
        if user not in json.loads(row["players"]):
            return "This user is not in the game"
    return False

### verifies that a kill is valid ###
def check_for_killed_error(code, user):
    with sqlite3.connect("database.db") as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        if cur.execute("SELECT count(*) FROM Games WHERE code = ? ", (code, )).fetchone()[0] == 0:
            return "This game has already ended."
        if user not in json.loads(cur.execute("SELECT * FROM Games WHERE code= ? ", (code, )).fetchone()["alive"]):
            return "You are already dead!"
    return False

### verifies that a purge is valid ###
def check_for_purge_error(code, user):
    with sqlite3.connect("database.db") as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        if cur.execute("SELECT count(*) FROM Games WHERE code = ? ", (code, )).fetchone()[0] == 0:
            return "This game has already ended."
        if user not in json.loads(cur.execute("SELECT * FROM Games WHERE code= ? ", (code, )).fetchone()["alive"]):
            return "This player is already dead!"
    return False

### verifies that a user is an actual player in the game ###
def check_if_game_complete(code):
    with sqlite3.connect("database.db") as con:  
        cur = con.cursor() 
        if cur.execute("SELECT count(*) FROM Games WHERE code = ? ", (code, )).fetchone()[0] > 0:
            return "active"
        if cur.execute("SELECT count(*) FROM PastGames WHERE code = ? ", (code, )).fetchone()[0] > 0:
            return "past"
    return False
