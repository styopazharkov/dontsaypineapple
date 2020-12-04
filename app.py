#####################################
#####################################
#### 2020 WORD ASSASSINS WEBSITE ####
#####################################
#####################################


### The following code is the imported packages ###
from flask import Flask, redirect, url_for, render_template, request, session, abort
import sqlite3, json
import checks, verifiers, maff
import hashing


### The following code creates the app variable and assigns a secret key for the session dictionary ###
app = Flask(__name__)
app.secret_key = "this is an arbitrary string"


#### PAGE ROUTING BELOW THIS LINE ####

### index page route. ###
## The main page of the website. Has: personal user input box, create new user button ##
@app.route('/')
def index():
    session['loggedIn'] = False
    session['password'] = ""
    try:
        error = session.pop('error')
    except KeyError:
        error = ""
    try:
        user = session.pop('user')
    except KeyError:
        user = ""
    
    return render_template('index.html', error = error, user = user)

### _login helper route ###
## This helper page is accessed when a personal user is entered from the index page. ##
## It checks that the user is good and then redirects to the home page of the user ##
## If the user is not good, the user is redirected back to the index page with an 'invalid user' message ## 
@app.route('/_login', methods=['POST'])
def _login():
    user = request.form['user']
    session['user'] = user
    password = request.form['password']
    hashPass = hashing.hashpass(password)
    error = checks.check_for_login_error(user, password)
    if error:
        session['error']=error
        return redirect(url_for('index'))
    else:
        session['loggedIn'] = True
        session['password'] = password
        return redirect(url_for('home'))
            
### signup page route ###
## Page for creating a new user. ##
## Has: user repeatuser and name input boxes, back button (TODO), signup button ## 
@app.route('/signup/')
def signup():
    try:
        error, user, name = session.pop('error'), session.pop('user'), session.pop('name')
    except KeyError:
        error, user, name = "", "", ""
    return render_template('signup.html', error = error, user = user, name = name)

### _signup helper route ###
## This helper page is accessed when info is entered from the signup page. ##
## It checks that the info is good, adds the info to the database, and redirects to the home page ##
@app.route('/_signup', methods = ['POST'])
def _signup():
    user = request.form["user"]
    password = request.form["password"]
    hashPass = hashing.hashpass(password) ##TODO this needs to be hashed
    passwordRepeat = request.form["passwordRepeat"]
    name = request.form["name"] 
    games = json.dumps([])
    pastGames = json.dumps([])
    stats = json.dumps({"played": 0, "survivalWins": 0, "killWins": 0, "kills": 0})
    error = checks.check_for_signup_error(user, password, passwordRepeat, name)
    if error:
        session['error']=error
        session['user']=user
        session['name']=name
        return redirect(url_for('signup'))
    else:
        with sqlite3.connect("database.db") as con:  
            cur = con.cursor() 
            cur.execute("INSERT into Players (user, password, name, games, pastGames, stats) values (?, ?, ?, ?, ?, ?)", (user, hashPass, name, games, pastGames, stats))   #creates new user
            con.commit()
        session['loggedIn'] = True
        session['user'] = user
        session['password'] = password
        return redirect(url_for('home'))
### home page route ###
## Home page of a specific user ##
## Has: (TODO) welcome, active games, past games, join new and create buttons, edit pf button, logout button ##
@app.route('/home')
def home():
    if not verifiers.verify_session_logged_in():
        session['error'] = "You cant access home page before logging in!"
        return redirect(url_for('index'))

    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row  
        cur = con.cursor()  

        cur.execute("SELECT * from Players WHERE user = ?", (session['user'], )) 
        name = cur.fetchone()["name"]
        cur.execute("SELECT * from Players WHERE user = ?", (session['user'], )) 
        games = json.loads(cur.fetchone()["games"])
    return render_template('home.html', name=name, user=session['user'], games = games)

### join page ###
@app.route('/join/')
def join():
    if not verifiers.verify_session_logged_in():
        session['error']="You cant access join page before logging in!"
        return redirect(url_for('index'))

    try:
        error = session.pop('error')
    except KeyError:
        error = ""
    return render_template('join.html', error = error)

### join helper route ###
@app.route('/_join/', methods = ['POST'])
def _join():
    if not verifiers.verify_session_logged_in():
        session['error']="You cant access _join page before logging in!"
        return redirect(url_for('index'))

    code = request.form['code']
    error = checks.check_for_join_error(code)
    if error:
        session['error'] = error
        return redirect(url_for('join'))
    else:
        with sqlite3.connect("database.db") as con:  
            con.row_factory = sqlite3.Row
            cur = con.cursor() 
            cur.execute("SELECT * from Games WHERE code = ? ", (code, ))
            players = json.dumps(json.loads(cur.fetchone()["players"])+[session['user']]) #adds user to the player list of the game
            cur.execute("UPDATE Games SET players = ? WHERE code = ? ", (players, code))
            cur.execute("SELECT * from Players WHERE user = ? ", (session['user'], ))
            games = json.dumps(json.loads(cur.fetchone()["games"])+[code]) #adds game to the games list of the user
            cur.execute("UPDATE Players SET games = ? WHERE user = ? ", (games, session['user']))
        return redirect(url_for('game', code = code))

### create page ###
@app.route('/create/')
def create():
    if not verifiers.verify_session_logged_in():
        session['error']="You cant access create page before logging in!"
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
    if not verifiers.verify_session_logged_in():
        session['error']="You cant access _create page before logging in!"
        return redirect(url_for('index'))

    code = request.form['code']
    name = request.form['name']
    settings = {}
    settings['difficulty'] = request.form['difficulty']
    settings = json.dumps(settings)
    host = session['user']
    started = 0
    players = json.dumps([session['user']])
    alive = json.dumps([])
    purged = json.dumps([])
    targets = json.dumps({})
    killCount = json.dumps({})
    killLog = json.dumps([])
    #winner is not set

    error = checks.check_for_create_error(code, name, settings)
    if error:
        session['error'] = error
        session['code'] = code
        session['name'] = name
        return redirect(url_for('create'))
    else:
        with sqlite3.connect("database.db") as con:  
            con.row_factory = sqlite3.Row
            cur = con.cursor() 

            cur.execute("INSERT into Games (code, name, settings, host, started, players, alive, purged, targets, killCount, killLog) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (code, name, settings, host, started, players, alive, purged, targets, killCount, killLog))   #creates new user
            con.commit()

            cur.execute("SELECT * from Players WHERE user = ? ", (session['user'], ))
            games = json.dumps(json.loads(cur.fetchone()["games"])+[code]) #adds game to the games list of the user
            cur.execute("UPDATE Players SET games = ? WHERE user = ? ", (games, session['user']))
        return redirect(url_for('game', code = code))

### game page route ###
## Page for viewing a specific game. Accessible from home page ##
## If user is the host, has: list of players, start button, kick button, back button ##
## If user is not host, has: list of players, leave game button, back button ##
@app.route('/game/<code>')
def game(code):
    if not verifiers.verify_session_logged_in():
        session['error']="You cant access game page before logging in!"
        return redirect(url_for('index'))
    
    completeness = checks.check_if_game_complete(code)
    if completeness == "active":
        return activeGame(code)
    elif completeness == "past":
        return pastGame(code)
    else:
        return redirect(url_for('home'))

def pastGame(code):
    data={}
    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        gameRow = cur.execute("SELECT * FROM PastGames WHERE code = ? ", (code, )).fetchone()
        data['code'] = code
        data['user'] = session['user']
        data['title'] = gameRow['name']
        data['settings'] = gameRow['settings']
        data['host'] = gameRow['host']
        data['players'] = json.loads(gameRow['players'])
        data['survivalWinner'] = gameRow['survivalWinner']
        data['killWinners'] = gameRow['killWinners']
        data['killLog'] = json.loads(gameRow['killLog'])
    return render_template('pastGame.html', data = data)

def activeGame(code):
    if not verifiers.verify_user_in_game(session['user'], code):
        return redirect(url_for('home'))
    
    try:
        error = session.pop('error')
    except KeyError:
        error = ""

    data={}
    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        gameRow = cur.execute("SELECT * FROM Games WHERE code = ? ", (code, )).fetchone()
        data['code'] = code
        data['user'] = session['user']
        data['title'] = gameRow['name']
        data['admin'] = (gameRow['host'] == session['user'])
        data['started'] = gameRow['started']
        data['settings'] = gameRow['settings']
        data['host'] = gameRow['host']
        data['players'] = json.loads(gameRow['players'])
        data['numberOfPlayers'] = len(data['players'])
        data['alive'] = json.loads(gameRow['alive'])
        data['purged'] = json.loads(gameRow['purged'])
        if gameRow['started']:
            data['word'] = json.loads(gameRow['targets'])[session['user']]['word']
            data['target'] = json.loads(gameRow['targets'])[session['user']]['target']
        data['isAlive'] = session['user'] in gameRow['alive']

    return render_template('game.html', data = data, error=error)
### _start helper route starts a game that isnt started ###
## only possible by host ##
@app.route('/_start/<code>', methods = ['POST'])
def _start(code):
    if not verifiers.verify_session_logged_in():
        session['error']="You cant access _start page before logging in!"
        return redirect(url_for('index'))

    if not verifiers.verify_host(code):
        return redirect(url_for('home'))

    error = checks.check_for_start_error(code)
    if error:
        session['error'] = error
        return redirect(url_for('game', code = code))

    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row
        cur = con.cursor() 
        row = cur.execute("SELECT * from Games WHERE code = ? ", (code, )).fetchone()
        started = 1
        alive = row['players']
        players = json.loads(row["players"])
        settings = json.loads(row['settings'])
        targets = {}
        n=len(players)
        permutation = maff.random_permutation(n)
        for i in range(n):
            #TODO implement words here
            targets[players[permutation[i]]] = {"word": maff.get_word(settings), "target": players[permutation[(i+1)%n]], "assassin": players[permutation[i-1]]}
        targets = json.dumps(targets)
        killCount={}
        for player in players:
            killCount[player] = 0
        killCount = json.dumps(killCount)
        cur.execute("UPDATE Games SET started = ?,  alive = ?, targets = ?, killCount = ? WHERE code = ? ", (started, alive, targets, killCount, code))
    return redirect(url_for('game', code = code))

### _cancel helper route cancels a game that isn't yet started ###
## only possible by host ##
@app.route('/_cancel/<code>', methods = ['POST'])
def _cancel(code):
    if not verifiers.verify_session_logged_in():
        session['error']="You cant access _cancel page before logging in!"
        return redirect(url_for('index'))

    if not verifiers.verify_host(code):
        return redirect(url_for('home'))
    
    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row
        cur = con.cursor() 
        players = json.loads(cur.execute("SELECT * from Games WHERE code = ? ", (code, )).fetchone()['players'])
        for player in players: #delets the game from each players game list
            cur.execute("SELECT * from Players WHERE user = ? ", (player, ))
            games = json.loads(cur.fetchone()["games"])
            games.remove(code) #removes game to the games list of the user
            games = json.dumps(games) 
            cur.execute("UPDATE Players SET games = ? WHERE user = ? ", (games, player))

        cur.execute("DELETE FROM Games WHERE code = ? ", (code, )) #deletes the game from the games database
    return redirect(url_for('home'))


### _kick helper route removes a player from a game that hasn't started ###
## only possible by admin ##
@app.route('/_kick/<code>/<user>', methods = ['POST'])
def _kick(code, user):

    if not verifiers.verify_session_logged_in():
        session['error']="You cant access _kick page before logging in!"
        return redirect(url_for('index'))

    if not verifiers.verify_host(code) or not verifiers.verify_user_in_game(user, code) or user == session['user']:
        session['error']="something is not right! (_kick page error)"
        return redirect(url_for('index'))

    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row
        cur = con.cursor() 
        cur.execute("SELECT * from Players WHERE user = ? ", (user, ))
        games = json.loads(cur.fetchone()["games"])
        games.remove(code) #removes game from the games list of the user
        games = json.dumps(games) 
        cur.execute("UPDATE Players SET games = ? WHERE user = ? ", (games, user))

        cur.execute("SELECT * from Games WHERE code = ? ", (code, ))
        players = json.loads(cur.fetchone()["players"])
        players.remove(user)  #removes user from the player list of the game
        players = json.dumps(players) 
        cur.execute("UPDATE Games SET players = ? WHERE code = ? ", (players, code))
    return redirect(url_for('game', code = code))
    
@app.route('/_killed/<code>', methods = ['POST'])
def _killed(code):
    if not verifiers.verify_session_logged_in():
        session['error']="You cant access _killed page before logging in!"
        return redirect(url_for('index'))
    
    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row
        cur = con.cursor() 
        user = session['user']
        row = cur.execute("SELECT * from Games WHERE code = ? ", (code, )).fetchone()
        alive = json.loads(row["alive"])
        alive.remove(user)  #removes user from the alive list of the game
        targets = maff.edit_targets_on_kill(user, json.loads(row['targets']))
        killCount = json.loads(row['killCount'])
        killCount[targets[user]['assassin']] += 1 #adds to assassin's kill count
        killLog = json.loads(row['killLog'])+[(targets[user]['assassin'], "killed", user, targets[user]['word'])] #adds to kill log
        if len(alive) > 1: #if the game is not yet over
            alive, targets, killCount, killLog = json.dumps(alive), json.dumps(targets), json.dumps(killCount), json.dumps(killLog) #json encripts everything
            cur.execute("UPDATE Games SET alive = ?, targets = ?, killCount = ?, killLog = ? WHERE code = ? ", (alive, targets, killCount, killLog, code)) 
        else:  #the game has just finished
            players = json.loads(row['players'])
            survivalWinner = alive[0]
            killWinners = maff.create_killWinners(players, killCount)
            distribute_kills_and_wins(cur, players, killCount, survivalWinner, killWinners)
            players, killWinners, killLog = json.dumps(players), json.dumps(killWinners), json.dumps(killLog)
            cur.execute("INSERT into PastGames (code, name, settings, host, players, survivalWinner, killWinners, killLog) values (?, ?, ?, ?, ?, ?, ?, ?)",  (code, row['name'], row['settings'], row['host'], players, survivalWinner, killWinners, killLog))   #adds to pastgames
            con.commit()
            cur.execute("DELETE FROM Games WHERE code = ? ", (code, )) #deletes from games

    return redirect(url_for('game', code = code))

### purge page for purging a player by game host ###
@app.route('/_purge/<code>/<user>', methods = ['POST'])
def _purge(code, user):
    if not verifiers.verify_session_logged_in():
        session['error']="You cant access _purge page before logging in!"
        return redirect(url_for('index'))

    if not verifiers.verify_host(code) or not verifiers.verify_user_in_game(user, code) or user == session['user']:
        session['error']="something is not right! (_purge)"
        return redirect(url_for('index'))

    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        row = cur.execute("SELECT * from Games WHERE code = ? ", (code, )).fetchone()
        alive = json.loads(row["alive"])
        alive.remove(user)  #removes user from the alive list of the game
        purged = json.dumps(json.loads(row["purged"])+[user]) #adds user to the purged list of the game
        targets = maff.edit_targets_on_kill(user, json.loads(row['targets']))
        killLog = json.loads(row['killLog'])+[(targets[user]['assassin'], "purged", user, targets[user]['word'])] #adds to kill log
        if len(alive) > 1:
            alive, targets,  killLog = json.dumps(alive), json.dumps(targets), json.dumps(killLog) #json encripts everything
            cur.execute("UPDATE Games SET alive = ?, targets = ?, purged = ?, killLog = ? WHERE code = ? ", (alive, targets, purged, killLog, code))
        else:
            players = json.loads(row['players'])
            survivalWinner = alive[0]
            killCount = json.loads(row['killCount'])
            killWinners = maff.create_killWinners(players, killCount)
            distribute_kills_and_wins(cur, players, killCount, survivalWinner, killWinners)
            players, killWinners, killLog = json.dumps(players), json.dumps(killWinners), json.dumps(killLog)
            cur.execute("INSERT into PastGames (code, name, settings, host, players, survivalWinner, killWinners, killLog) values (?, ?, ?, ?, ?, ?, ?, ?)",  (code, row['name'], row['settings'], row['host'], players, survivalWinner, killWinners, killLog))   #adds to pastgames
            con.commit()
            cur.execute("DELETE FROM Games WHERE code = ? ", (code, )) #deletes from games
    return redirect(url_for('game', code = code))

def distribute_kills_and_wins(cur, players, killCount, survivalWinner, killWinners):
    for player in players:
        stats = json.loads(cur.execute("SELECT * from Players WHERE user = ? ", (player, )).fetchone()["stats"])
        stats["played"] += 1
        stats["kills"] += killCount[player]
        stats["survivalWins"] += int(player == survivalWinner)
        stats["killWins"] += (int(player in killWinners)/len(killWinners))
        stats=json.dumps(stats)
        cur.execute("UPDATE Players SET stats = ? WHERE user = ? ", (stats, player))



#### DEBUG ROUTING BELOW THIS LINE ####

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

        cur.execute("SELECT * from pastGames")   
        pastRows = cur.fetchall()   #rows of the pastGames table

    return render_template('debug.html', playerRows = playerRows, gameRows = gameRows, pastRows=pastRows)

#### MAIN APP RUN BELOW THIS LINE ####

if __name__ == "__main__":
    app.run(debug = True) #set debug to false if you don't want auto updating