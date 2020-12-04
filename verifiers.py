#### This file contains verifier helper functions. They all return a boolean value ####
from flask import  session
import sqlite3, json
import hashing

### verfier that a user is logged in on a page ###
def verify_session_logged_in():
    if not (session.get('loggedIn') and session.get('user') and session.get('password')): #checks that loggedIn and user session variables exist
        return False
    with sqlite3.connect("database.db") as con:  #checks that the user is an actual user in the database
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        if cur.execute("SELECT count(*) FROM Players WHERE user = ? ", (session['user'], )).fetchone()[0] == 0: #checks that user exists 
            return False
        if not hashing.verify(session['password'], cur.execute("SELECT * FROM Players WHERE user = ? ", (session['user'], )).fetchone()['password']) : # checks that passwords match TODO: hashpass
            return False
    return session['loggedIn'] #makes sure logged in variable is set to true

### verifies that a user is an actual player in the game ###
def verify_user_in_game(user, code):
    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row
        cur = con.cursor() 
        if cur.execute("SELECT count(*) FROM Games WHERE code = ? ", (code, )).fetchone()[0] == 0:
            return False
        return user in cur.execute("SELECT * FROM Games WHERE code = ? ", (code, )).fetchone()['players']

## verifies that the session user is the host ##
def verify_host(code):
        with sqlite3.connect("database.db") as con:  
            con.row_factory = sqlite3.Row
            cur = con.cursor() 
            if cur.execute("SELECT count(*) FROM Games WHERE code = ? ", (code, )).fetchone()[0] == 0:
                return False
            return session['user'] == cur.execute("SELECT * FROM Games WHERE code = ? ", (code, )).fetchone()['host']
