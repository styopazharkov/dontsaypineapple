from flask import  session
import sqlite3, json
import hashing

### verifier that checks that a user is good to log in with. makes sure it's long and is in the database ###
## returns an error message if there is an error. False if there is no error ##
def check_for_login_error(user, password):
    if len(user) < 5:
        return "The username can't be less than 5 characters long"
    if len(password) < 5:
        return "The password can't be less than 5 characters long"
    with sqlite3.connect("database.db") as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        if cur.execute("SELECT count(*) FROM Players WHERE user= ? ", (user, )).fetchone()[0] == 0: #checks that username exsts
            return "no such user exists"
        if not hashing.verify(password, cur.execute("SELECT * FROM Players WHERE user = ? ", (session['user'], )).fetchone()['password']): # checks that passwords match
            return "The username or password is wrong"
    return  False
        
### verifier that checks that a username, password and name are good to sign up with. makes sure it's long and is in the database ###
## returns an error message if there is an error. False if there is no error ##
def check_for_signup_error(user, password, passwordRepeat, name):
    #TODO: check that the username only contains normal characters
    if len(user) < 5:
        return "The username can't be less than 5 characters long."
    if len(user) > 20:
        return "The username can't be more than 20 characters long."
    if len(password) < 5:
        return "The password can't be less than 5 characters long."
    if password != passwordRepeat:
        return "The passwords must match."
    if len(name.strip()) == 0:
        return "You must have a name!"
    with sqlite3.connect("database.db") as con:
        cur = con.cursor()
        if cur.execute("SELECT count(*) FROM Players WHERE user= ? ", (user, )).fetchone()[0] > 0:
            return "Oh no! Someone already took this username."
    return  False

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
def check_for_create_error(code, name):
    if len(code)<5:
        return "game code must be at least 5 characters long"
    if len(name.strip())==0:
        return "your game must have a name"
    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row
        cur = con.cursor() 
        if cur.execute("SELECT count(*) FROM Games WHERE code = ? ", (code, )).fetchone()[0] > 0:
            return "a game with this code already exists"
    return False

def check_for_start_error(code):
    with sqlite3.connect("database.db") as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        if len(json.loads(cur.execute("SELECT * FROM Games WHERE code= ? ", (code, )).fetchone()["players"])) < 2:
            return "You need at least 2 players to play!"
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
