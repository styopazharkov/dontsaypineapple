#######################################
#######################################
#### 2020 DONT SAY PINEAPPLE WEBSITE ####
#######################################
#######################################


### The following code is the imported packages ###
from flask import Flask, redirect, url_for, render_template, request, session, abort
import sqlite3, json
import checks, verifiers, maff, fetchers
import hashing


### The following code creates the app variable and assigns a secret key for the session dictionary ###
app = Flask(__name__)
app.secret_key = "An arbitrary key for Don't Say Pineapple"


#### PAGE ROUTING BELOW THIS LINE ####

### index page route. ###
## The main page of the website. Has: username input box, sign up button ##
@app.route('/')
def index():
    session['loggedIn'] = False #resets login session var
    session['password'] = "" #resets password session var
    try: #checks if there is an error message to show
        error = session.pop('error') 
    except KeyError:
        error = ""
    try: #checks if there is a username stored in session to remember
        user = session.pop('user')
    except KeyError:
        user = ""
    return render_template('index.html', error = error, user = user) #renders html page

### _login helper route ###
## This helper page is accessed when a username and password are entered from the index page. ##
## It checks that the username and password are good and then redirects to the home page of the user ##
## If the credentials are not good, the user is redirected back to the index page with an 'invalid user' message ## 
@app.route('/_login', methods=['POST'])
def _login():
    try: #tries to get username and password
        user = request.form['user']
        password = request.form['password']
    except KeyError: #only runs if someone messes with the html
        user, password = "", ""

    session['user'] = user
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
## Has: user password repeatpassword and name input boxes, back button, signup button ## 
@app.route('/signup/')
def signup():
    try: # checks if there is an error.
        error, user, name = session.pop('error'), session.pop('user'), session.pop('name')
    except KeyError:
        error, user, name = "", "", ""
    return render_template('signup.html', error = error, user = user, name = name)

### _signup helper route ###
## This helper page is accessed when info is entered from the signup page. ##
## It checks that the info is good, adds the info to the database, and redirects to the home page ##
@app.route('/_signup', methods = ['POST'])
def _signup():
    try: #tries to get info for form
        user = request.form["user"]
        password = request.form["password"]
        passwordRepeat = request.form["passwordRepeat"]
        name = request.form["name"] 
    except KeyError: #only runs is someone messes with the html
        password, passwordRepeat, user, name = "", "", "", ""
    
    error = checks.check_for_signup_error(user, password, passwordRepeat, name)
    if error:
        session['error']=error
        session['user']=user
        session['name']=name
        return redirect(url_for('signup'))
    else:
        hashPass = hashing.hashpass(password)
        games = json.dumps([])
        pastGames = json.dumps([])
        stats = json.dumps({"played": 0, "survivalWins": 0, "killWins": 0, "kills": 0})
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
## Has: welcome, active games, past games, join new and create buttons, edit pf button (TODO), logout button ##
@app.route('/home')
def home():
    if not verifiers.verify_session_logged_in(): #verifies that user is logged in
        session['error'] = "You cant access home page before logging in!"
        return redirect(url_for('index'))

    try:
        error = session.pop('error')
    except KeyError:
        error = ""
    
    data = {} #data that will be put into html template
    data['user'] = session['user']
    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row  
        cur = con.cursor()  
        row = cur.execute("SELECT * from Players WHERE user = ?", (session['user'], )) .fetchone()
        data['name'] = row["name"]
        data['status'] = row["status"]
        data['activeGames'], data['pastGames'] = [], []
        games = json.loads(row["games"])
        for game in games: #sorts games into active and past ones
            if checks.check_if_game_complete(game) == 'active':
                data['activeGames'].append(fetchers.get_active_button_info(game))
            else:
                data['pastGames'].append(fetchers.get_past_button_info(game))
        data['stats'] = json.loads(row['stats'])
    return render_template('home.html', data=data, error = error)

### helper route for renaming and setting the status ###
@app.route('/_rename', methods = ['POST'])
def _rename():
    try: #tries to get info from form
        name = request.form["name"]
        status = request.form["status"]
    except KeyError: #only runs is someone messes with the html
        name, status = "", ""
    
    error = checks.check_for_rename_error(name, status)
    if error:
        session['error'] = error
        return redirect(url_for('home'))

    with sqlite3.connect("database.db") as con:  
            con.row_factory = sqlite3.Row
            cur = con.cursor() 
            cur.execute("UPDATE Players SET name = ?, status = ? WHERE user = ? ", (name, status, session['user']))
            con.commit()
    return redirect(url_for('home'))


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

    try: #tries to get code
        code = request.form['code']
    except KeyError: #only runs if someone messes with html
        code = ""

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
            con.commit()
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

    settings = {}
    try: #tries to get info
        code = request.form['code']
        name = request.form['name']
        settings['difficulty'] = request.form['difficulty']
        settings['passon'] = request.form['passon']
    except KeyError: #this only runs is someone messes with the html
        code, name, settings['difficulty'], settings['passon'] = "", "", "", ""

    error = checks.check_for_create_error(code, name, settings)
    if error:
        session['error'] = error
        session['code'] = code
        session['name'] = name
        return redirect(url_for('create'))
    else:
        host, started, players = session['user'], 0, json.dumps([session['user']]) #sets defaults
        alive, purged, targets, killCount, killLog = json.dumps([]), json.dumps([]), json.dumps({}), json.dumps({}), json.dumps([]) #sets defaults
        settings = json.dumps(settings)
        with sqlite3.connect("database.db") as con:  
            con.row_factory = sqlite3.Row
            cur = con.cursor() 
            cur.execute("INSERT into Games (code, name, settings, host, started, players, alive, purged, targets, killCount, killLog) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (code, name, settings, host, started, players, alive, purged, targets, killCount, killLog))   #creates new user
            cur.execute("SELECT * from Players WHERE user = ? ", (session['user'], ))
            games = json.dumps(json.loads(cur.fetchone()["games"])+[code]) #adds game to the games list of the user
            cur.execute("UPDATE Players SET games = ? WHERE user = ? ", (games, session['user']))
            con.commit()
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

### helper function for game. runs if the game is active ###
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

### helper function for game. runs is the game is over ###
def pastGame(code):
    try:
        error = session.pop('error')
    except KeyError:
        error = ""
    data={}
    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        gameRow = cur.execute("SELECT * FROM PastGames WHERE code = ? ", (code, )).fetchone()
        data['code'] = code
        data['user'] = session['user']
        data['title'] = gameRow['name']
        data['settings'] = json.loads(gameRow['settings'])
        data['host'] = gameRow['host']
        data['survivalWinner'] = {'code': gameRow['survivalWinner'], 'name': fetchers.get_name(cur, gameRow['survivalWinner'])}
        data['killWinners'] = [{'code': winner, 'name': fetchers.get_name(cur, winner)} for winner in json.loads(gameRow['killWinners'])]
        data['killLog'] = [{
            'method': entry[1],
            'victim': {'code': entry[2], 'name': fetchers.get_name(cur, entry[2])}, 
            'assassin': {'code': entry[0], 'name': fetchers.get_name(cur, entry[0])}, 
            'word': entry[3]
            } for entry in json.loads(gameRow['killLog'])]
    return render_template('pastGame.html', data = data, error=error)

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
        con.commit()
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

    error = checks.check_for_cancel_error(code)
    if error:
        session['error'] = error
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
        con.commit()
    return redirect(url_for('home'))

### _kick helper route removes a player from a game that hasn't started ###
## only possible by admin ##
@app.route('/_kick/<code>/<user>', methods = ['POST'])
def _kick(code, user):

    if not verifiers.verify_session_logged_in():
        session['error']="You cant access _kick page before logging in!"
        return redirect(url_for('index'))

    if not verifiers.verify_host(code) or user == session['user']:
        session['error']="Something is not right! (_kick page)"
        return redirect(url_for('game', code = code))

    error = checks.check_for_kick_error(code, user)
    if error:
        session['error'] = error
        return redirect(url_for('game', code = code))

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
        con.commit()
    return redirect(url_for('game', code = code))
    
### route for _killed helper function. This is called when a player presses the 'I was killed button' ###
@app.route('/_killed/<code>', methods = ['POST'])
def _killed(code):
    if not verifiers.verify_session_logged_in():
        session['error']="You cant access _killed page before logging in!"
        return redirect(url_for('index'))

    user = session['user']

    error = checks.check_for_killed_error(code, user)
    if error:
        session['error'] = error
        return redirect(url_for('game', code = code))

    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row
        cur = con.cursor() 
        row = cur.execute("SELECT * from Games WHERE code = ? ", (code, )).fetchone()
        alive = json.loads(row["alive"])
        alive.remove(user)  #removes user from the alive list of the game
        settings = json.loads(row['settings'])
        targets = maff.edit_targets_on_kill(user, json.loads(row['targets']), settings)
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
            fetchers.distribute_kills_and_wins(cur, players, killCount, survivalWinner, killWinners)
            players, killWinners, killLog = json.dumps(players), json.dumps(killWinners), json.dumps(killLog)
            cur.execute("INSERT into PastGames (code, name, settings, host, players, survivalWinner, killWinners, killLog) values (?, ?, ?, ?, ?, ?, ?, ?)",  (code, row['name'], row['settings'], row['host'], players, survivalWinner, killWinners, killLog))   #adds to pastgames
            cur.execute("DELETE FROM Games WHERE code = ? ", (code, )) #deletes from games
        con.commit()
    return redirect(url_for('game', code = code))

### purge page for purging a player by game host ###
@app.route('/_purge/<code>/<user>', methods = ['POST'])
def _purge(code, user):
    if not verifiers.verify_session_logged_in():
        session['error']="You cant access _purge page before logging in!"
        return redirect(url_for('index'))
    #TODO: check if page is updated with database. Catches if host tries purging without refreshing page
    if not verifiers.verify_host(code) or user == session['user']:
        session['error']="something is not right! (_purge)"
        return redirect(url_for('game', code = code))

    error = checks.check_for_purge_error(code, user)
    if error:
        session['error'] = error
        return redirect(url_for('game', code = code))
    
    with sqlite3.connect("database.db") as con:  
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        row = cur.execute("SELECT * from Games WHERE code = ? ", (code, )).fetchone()
        alive = json.loads(row["alive"])
        settings = json.loads(row['settings'])
        alive.remove(user)  #removes user from the alive list of the game
        purged = json.dumps(json.loads(row["purged"])+[user]) #adds user to the purged list of the game
        targets = maff.edit_targets_on_kill(user, json.loads(row['targets']), settings)
        killLog = json.loads(row['killLog'])+[(targets[user]['assassin'], "purged", user, targets[user]['word'])] #adds to kill log
        if len(alive) > 1:
            alive, targets,  killLog = json.dumps(alive), json.dumps(targets), json.dumps(killLog) #json encripts everything
            cur.execute("UPDATE Games SET alive = ?, targets = ?, purged = ?, killLog = ? WHERE code = ? ", (alive, targets, purged, killLog, code))
        else:
            players = json.loads(row['players'])
            survivalWinner = alive[0]
            killCount = json.loads(row['killCount'])
            killWinners = maff.create_killWinners(players, killCount)
            fetchers.distribute_kills_and_wins(cur, players, killCount, survivalWinner, killWinners)
            players, killWinners, killLog = json.dumps(players), json.dumps(killWinners), json.dumps(killLog)
            cur.execute("INSERT into PastGames (code, name, settings, host, players, survivalWinner, killWinners, killLog) values (?, ?, ?, ?, ?, ?, ?, ?)",  (code, row['name'], row['settings'], row['host'], players, survivalWinner, killWinners, killLog))   #adds to pastgames
            cur.execute("DELETE FROM Games WHERE code = ? ", (code, )) #deletes from games
            con.commit()
    return redirect(url_for('game', code = code))

@app.route('/rules/')
def rules():
    return render_template('rules.html')

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