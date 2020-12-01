#####################################
#####################################
#### 2020 WORD ASSASSINS WEBSITE ####
#####################################
#####################################




### The following code is the imported packages ###
from flask import Flask, redirect, url_for, render_template, request, session, abort
import sqlite3


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
    return render_template('index.html')


### _login helper route ###
## This helper page is accessed when a personal key is entered from the index page. ##
## It checks that the key is good and then redirects to the home page of the user ##
## If the key is not good, the user is redirected back to the index page with an 'invalid key' message (TODO) ## 
@app.route('/_login', methods=['POST'])
def _login():
    key = request.form['key']
    with sqlite3.connect("database.db") as con:  
        cur = con.cursor() 
        if cur.execute("SELECT count(*) FROM Players WHERE key= ? ", (key, )).fetchone()[0] > 0: #if key is in database
            session['loggedIn'] = True
            session['key'] = key
            return redirect(url_for('home'))
        else:
            abort(401)


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
    print(key) 
    keyRepeat = request.form["keyRepeat"]  
    name = request.form["name"]  
    with sqlite3.connect("database.db") as con:  
        cur = con.cursor() 
        cur.execute("INSERT into Players (key, name) values (?,?)",(key, name))   #creates new key
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
        return redirect(url_for('index'))
    
    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row  
        cur = con.cursor()  
        cur.execute("select * from Players")   
        rows = cur.fetchall()   
    return render_template('home.html', name=session['key'], rows=rows)




### join page route (TODO) ###
## Page for joining a new game. Accessible from home page ##
## Has: game code input box, join button, back button ##
@app.route('/join/')
def join():
    if not verify_session_logged_in():
        return redirect(url_for('index'))

    return render_template('join.html')


### create page route (TODO) ###
## Page for creating a new game. Accessible from home page ##
## Has: game code input box, a few game settings, create button, back button ##
@app.route('/create/')
def create():
    if not verify_session_logged_in():
        return redirect(url_for('index'))
    
    return render_template('create.html')


### game page route ###
## Page for viewing a specific game. Accessible from home page ##
## If user is the host, has: list of players, players in waiting room, start button, kick button, back button ##
## If user is not host, has: list of players, leave game button, back button ##
@app.route('/game/')
def game():
    if not verify_session_logged_in():
        return redirect(url_for('index'))

    return render_template('game.html')


#### HELPER FUNCTIONS BELOW THIS LINE ####

### verfier that a user is logged in on a page ###
## Makes sure the session variables are ##
def verify_session_logged_in():
    return session['loggedIn'] and session['key']
        


#### MAIN APP RUN BELOW THIS LINE ####

if __name__ == "__main__":
    app.run(debug = True)