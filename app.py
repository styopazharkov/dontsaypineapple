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
    error = request.args.get('error')
    return render_template('index.html', error = error)


### _login helper route ###
## This helper page is accessed when a personal key is entered from the index page. ##
## It checks that the key is good and then redirects to the home page of the user ##
## If the key is not good, the user is redirected back to the index page with an 'invalid key' message (TODO) ## 
@app.route('/_login', methods=['POST'])
def _login():
    key = request.form['key']
    error = check_valid_login_key(key)
    if error:
        return redirect(url_for('index', error = error))
    else:
        session['loggedIn'] = True
        session['key'] = key
        return redirect(url_for('home'))
            

def check_valid_login_key(key):
    if len(key) < 5:
        return "The key can't be less than 5 characters long"
    with sqlite3.connect("database.db") as con:
        cur = con.cursor()
        if cur.execute("SELECT count(*) FROM Players WHERE key= ? ", (key, )).fetchone()[0] == 0:
            return "This key does not exist"
    return  False



### signup page route ###
## Page for creating a new key. ##
## Has: key repeatKey and name input boxes, pfp input (TODO), back button (TODO), signup button ## 
@app.route('/signup/')
def signup():
    return render_template('signup.html')


### _signup helper route ###
## This helper page is accessed when info is entered from the signup page. ##
## It checks that the info is good (TODO), adds the info to the database, and redirects to the home page ##
@app.route('/_signup', methods = ['POST'])
def _signup():
    key = request.form["key"]
    keyRepeat = request.form["keyRepeat"]  
    name = request.form["name"]  
    games = json.dumps([])
    #TODO check that everything is valid
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
        return redirect(url_for('index', error="please enter your key!"))
    
    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row  
        cur = con.cursor()  

        cur.execute("SELECT * from Players")   
        rows = cur.fetchall()   #rows of the players database, delete later

        cur.execute("SELECT * from Players WHERE key = ?", (session['key'], )) 
        name = cur.fetchone()["name"]
    return render_template('home.html', name=name)



@app.route('/_join/', methods = ['POST'])
def _join():
    if not verify_session_logged_in():
        return redirect(url_for('index', error="please enter your key!"))

    code = request.form['code']
    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row
        cur = con.cursor() 
        if cur.execute("SELECT count(*) FROM Games WHERE code = ? ", (code, )).fetchone()[0] > 0: #if game code is in database
            cur.execute("SELECT * from Games WHERE code = ? ", (code, ))
            players = json.dumps(json.loads(cur.fetchone()["players"])+[session['key']]) #adds user to the player list of the game
            cur.execute("UPDATE Games SET players = ? WHERE code = ? ", (players, code))
            return redirect(url_for('game', code = code))
        else:
            abort(401)


### _create helper route ###
## This helper page is accessed when info is entered from the create page. ##
## It checks that the info is good, adds the info to the database, and redirects to the game page ##
@app.route('/_create',  methods = ['POST'])
def _create():
    if not verify_session_logged_in():
        return redirect(url_for('index', error="please enter your key!"))

    code = request.form["code"]
    name = request.form["name"]  
    host = session['key']
    started = 0
    players = json.dumps([session['key']])
    alive = json.dumps([])
    targets = json.dumps({})
    #winner is not set

    #TODO check that everything is valid
    with sqlite3.connect("database.db") as con:  
        cur = con.cursor() 
        cur.execute("INSERT into Games (code, name, host, started, players, alive, targets) values (?, ?, ?, ?, ?, ?, ?)", (code, name, host, started, players, alive, targets))   #creates new key
        con.commit()
    return redirect(url_for('game', code = code))

### game page route ###
## Page for viewing a specific game. Accessible from home page ##
## If user is the host, has: list of players, start button, kick button, back button ##
## If user is not host, has: list of players, leave game button, back button ##
@app.route('/game/<code>')
def game(code):
    if not verify_session_logged_in():
        return redirect(url_for('index', error="please enter your key!"))

    return render_template('game.html')


#### HELPER FUNCTIONS BELOW THIS LINE ####

### verfier that a user is logged in on a page ###
def verify_session_logged_in():
    return session['loggedIn'] and session['key']
## Makes sure the session variables are ##
        

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