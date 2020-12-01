##################################
# 2020 WORD ASSASSINS WEBSITE #
##################################

#the following line is the imported packages
from flask import Flask, redirect, url_for, render_template, request, session, abort
import sqlite3

#the following line creates the app variable
app = Flask(__name__)
app.secret_key = "this is an arbitrary string"

 
#The following code is the index page route.
@app.route('/')
def index():
    session['loggedIn'] = False
    session['key'] = ""
    return render_template('index.html')

#The following code is for the _login helper route
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


    

#The following code is the home page route.
@app.route('/home')
def home():
    #TODO: check that user is logged in
    con = sqlite3.connect("database.db")  
    con.row_factory = sqlite3.Row  
    cur = con.cursor()  
    cur.execute("select * from Players")   
    rows = cur.fetchall()   
    return render_template('home.html', name=session['key'], rows=rows)


#The following code is the signup page route.
@app.route('/signup/')
def signup():
    return render_template('signup.html')

@app.route('/_signup', methods = ['POST'])
def _signup():
    key = request.form["key"]  
    print(key) 
    keyRepeat = request.form["keyRepeat"]  
    #TODO: check that keyRepeat == key, check if user already exists, etc
    name = request.form["name"]  
    with sqlite3.connect("database.db") as con:  
        cur = con.cursor() 
        cur.execute("INSERT into Players (key, name) values (?,?)",(key, name))   #creates new key
        con.commit()
    session['loggedIn'] = True
    session['key'] = key
    return redirect(url_for('home'))


#The following code is the join page route.
@app.route('/join/')
def join():
    return "join"


#The following code is the create page route.
@app.route('/create/')
def create():
    return "create"

#The following code is the game page route.
@app.route('/game/')
def game():
    return "game"

if __name__ == "__main__":
    app.run(debug = True)