#####################################
#####################################
#### 2020 WORD ASSASSINS WEBSITE ####
#####################################
#####################################


### The following code is the imported packages ###
from flask import Flask, redirect, url_for, render_template, request, session, abort
import sqlite3, json


### The following code creates the app variable and assigns a secret key for the session dictionary ###
app = Flask(__name__)
app.secret_key = "this is an arbitrary string"


#### PAGE ROUTING BELOW THIS LINE ####


### index page route. ###
## The main page of the website. Has: personal key input box, create new key button ##
@app.route('/')
def index():
    session['loggedIn'] = False
    session['key'] = ""
    try:
        error = session.pop('error')
    except KeyError:
        error = ""
    return render_template('index.html', error = error)


### _login helper route ###
## This helper page is accessed when a personal key is entered from the index page. ##
## It checks that the key is good and then redirects to the home page of the user ##
## If the key is not good, the user is redirected back to the index page with an 'invalid key' message (TODO) ## 
@app.route('/_login', methods=['POST'])
def _login():
    key = request.form['key']
    error = check_for_login_error(key)
    if error:
        session['error']=error
        return redirect(url_for('index'))
    else:
        session['loggedIn'] = True
        session['key'] = key
        return redirect(url_for('home'))
            

### signup page route ###
## Page for creating a new key. ##
## Has: key repeatKey and name input boxes, pfp input (TODO), back button (TODO), signup button ## 
@app.route('/signup/')
def signup():
    try:
        error, name = session.pop('error'), session.pop('name')
    except KeyError:
        error, name = "", ""
    return render_template('signup.html', error = error, name = name)


### _signup helper route ###
## This helper page is accessed when info is entered from the signup page. ##
## It checks that the info is good, adds the info to the database, and redirects to the home page ##
@app.route('/_signup', methods = ['POST'])
def _signup():
    key = request.form["key"]
    keyRepeat = request.form["keyRepeat"]  
    name = request.form["name"]  
    games = json.dumps([])
    error = check_for_signup_error(key, keyRepeat, name)
    if error:
        session['error']=error
        session['name']=name
        return redirect(url_for('signup'))
    else:
        with sqlite3.connect("database.db") as con:  
            cur = con.cursor() 
            cur.execute("INSERT into Players (key, name, games) values (?, ?, ?)", (key, name, games))   #creates new key
            con.commit()
        session['loggedIn'] = True
        session['key'] = key
        return redirect(url_for('home'))
   

### home page route ###
## Home page of a specific user ##
## Has: (TODO) welcome, active games, past games, join new and create buttons, edit pf button, logout button ##
@app.route('/home')
def home():
    if not verify_session_logged_in():
        session['error'] = "please enter your key!"
        return redirect(url_for('index'))


    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row  
        cur = con.cursor()  

        cur.execute("SELECT * from Players WHERE key = ?", (session['key'], )) 
        name = cur.fetchone()["name"]
        cur.execute("SELECT * from Players WHERE key = ?", (session['key'], )) 
        games = json.loads(cur.fetchone()["games"])
    return render_template('home.html', name=name, games = games)

### join page ###
@app.route('/join/')
def join():
    if not verify_session_logged_in():
        session['error']="please enter your key!"
        return redirect(url_for('index'))

    try:
        error = session.pop('error')
    except KeyError:
        error = ""
    return render_template('join.html', error = error)

### join helper route ###
@app.route('/_join/', methods = ['POST'])
def _join():
    if not verify_session_logged_in():
        session['error']="please enter your key!"
        return redirect(url_for('index'))

    code = request.form['code']
    error = check_for_join_error(code)
    if error:
        session['error'] = error
        return redirect(url_for('join'))
    else:
        with sqlite3.connect("database.db") as con:  
            con.row_factory = sqlite3.Row
            cur = con.cursor() 
            cur.execute("SELECT * from Games WHERE code = ? ", (code, ))
            players = json.dumps(json.loads(cur.fetchone()["players"])+[session['key']]) #adds user to the player list of the game
            cur.execute("UPDATE Games SET players = ? WHERE code = ? ", (players, code))

            cur.execute("SELECT * from Players WHERE key = ? ", (session['key'], ))
            games = json.dumps(json.loads(cur.fetchone()["games"])+[code]) #adds game to the games list of the user
            cur.execute("UPDATE Players SET games = ? WHERE key = ? ", (games, session['key']))
        return redirect(url_for('game', code = code))

### create page ###
@app.route('/create/')
def create():
    if not verify_session_logged_in():
        session['error']="please enter your key!"
        return redirect(url_for('index'))
    
    try:
        error, code, name = session.pop('error'), session.pop('code'), session.pop('name')
    except KeyError:
        error, code, name = "", "", ""
    return render_template('create.html', error = error, code = code, name=name)

### _create helper route ###
## This helper page is accessed when info is entered from the create page. ##
## It checks that the info is good, adds the info to the database, and redirects to the game page ##
@app.route('/_create',  methods = ['POST'])
def _create():
    if not verify_session_logged_in():
        session['error']="please enter your key!"
        return redirect(url_for('index'))

    code = request.form["code"]
    name = request.form["name"]  
    host = session['key']
    started = 0
    players = json.dumps([session['key']])
    alive = json.dumps([])
    targets = json.dumps({})
    #winner is not set

    error = check_for_create_error(code, name)
    if error:
        session['error'] = error
        session['code'] = code
        session['name'] = name
        return redirect(url_for('create'))
    else:
        with sqlite3.connect("database.db") as con:  
            con.row_factory = sqlite3.Row
            cur = con.cursor() 

            cur.execute("INSERT into Games (code, name, host, started, players, alive, targets) values (?, ?, ?, ?, ?, ?, ?)", (code, name, host, started, players, alive, targets))   #creates new key
            con.commit()

            cur.execute("SELECT * from Players WHERE key = ? ", (session['key'], ))
            games = json.dumps(json.loads(cur.fetchone()["games"])+[code]) #adds game to the games list of the user
            cur.execute("UPDATE Players SET games = ? WHERE key = ? ", (games, session['key']))
        return redirect(url_for('game', code = code))



### game page route ###
## Page for viewing a specific game. Accessible from home page ##
## If user is the host, has: list of players, start button, kick button, back button ##
## If user is not host, has: list of players, leave game button, back button ##
@app.route('/game/<code>')
def game(code):
    if not verify_session_logged_in():
        session['error']="please enter your key!"
        return redirect(url_for('index'))
    
    if not verify_user_in_game(code):
        #(TODO) add error message
        return redirect(url_for('home'))

    data={"code": code}

    return render_template('game.html', data = data)


#### HELPER FUNCTIONS BELOW THIS LINE ####

### verfier that a user is logged in on a page ###
def verify_session_logged_in():
    if not (session.get('loggedIn') and session.get('key')): #checks that loggedIn and key session variables exist
        return False
    with sqlite3.connect("database.db") as con:  #checks that the key is an actual user in the database
        con.row_factory = sqlite3.Row
        cur = con.cursor() 
        if cur.execute("SELECT count(*) FROM Players WHERE key = ? ", (session['key'], )).fetchone()[0] == 0:
            return False
    return session['loggedIn'] #makes sure logged in variable is set to true

### verifies that a user is an actual player in the game ###
def verify_user_in_game(code):
    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row
        cur = con.cursor() 
        if cur.execute("SELECT count(*) FROM Games WHERE code = ? ", (code, )).fetchone()[0] == 0:
            return False
        return session['key'] in cur.execute("SELECT * FROM Games WHERE code = ? ", (code, )).fetchone()['players']

### verifier that checks that a key is good to log in with. makes sure it's long and is in the database ###
## returns an error message if there is an error. False if there is no error ##
def check_for_login_error(key):
    if len(key) < 5:
        return "The key can't be less than 5 characters long"
    with sqlite3.connect("database.db") as con:
        cur = con.cursor()
        if cur.execute("SELECT count(*) FROM Players WHERE key= ? ", (key, )).fetchone()[0] == 0:
            return "This key does not exist"
    return  False
        
### verifier that checks that a key and name are good to sign up with. makes sure it's long and is in the database ###
## returns an error message if there is an error. False if there is no error ##
def check_for_signup_error(key, keyRepeat, name):
    if len(key) < 5:
        return "The key can't be less than 5 characters long."
    if key != keyRepeat:
        return "The keys must match"
    if len(name.strip()) == 0:
        return "You must have a name!"
    with sqlite3.connect("database.db") as con:
        cur = con.cursor()
        if cur.execute("SELECT count(*) FROM Players WHERE key= ? ", (key, )).fetchone()[0] > 0:
            return "Oh no! Someone already took this key."
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
        if session['key'] in cur.execute("SELECT * FROM Games WHERE code = ? ", (code, )).fetchone()['players']:
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

#### DEBUG CODE BELOW THIS LINE ####

### debugging page with database tables ###
@app.route('/debug/')
def debug():
    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row  
        cur = con.cursor()  

        cur.execute("SELECT * from Players")   
        playerRows = cur.fetchall()   #rows of the Players table

        cur.execute("SELECT * from Games")   
        gameRows = cur.fetchall()   #rows of the Games table

    return render_template('debug.html', playerRows = playerRows, gameRows = gameRows)

#### MAIN APP RUN BELOW THIS LINE ####

if __name__ == "__main__":
    app.run(debug = True) #set debug to false if you don't want auto updating