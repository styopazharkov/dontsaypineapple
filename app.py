#######################################
#######################################
#### 2020 DONT SAY PINEAPPLE WEBSITE ####
#######################################
#######################################


### The following code is the imported packages ###
from flask import Flask, redirect, url_for, render_template, request, session, abort
import json, os
import hashing
from flask_sqlalchemy import SQLAlchemy

### The following code creates the app variable and assigns a secret key for the session dictionary ###
## It also creates the database using sqlalchemy ###
app = Flask(__name__)
app.secret_key = "An arbitrary key for Don't Say Pineapple"

app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
### The folowing code imports sqlalchemy table objects ###
from models import Player, PastGame, Game
import checks, verifiers, maff, fetchers

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
    try: #checks if there is a theme stored in session to remember
        theme = session['theme']
    except KeyError:
        theme = "0"
    return render_template('index.html', error = error, user = user, theme = theme) #renders html page

### _login helper route ###
## This helper page is accessed when a username and password are entered from the index page. ##
## It checks that the username and password are good and then redirects to the home page of the user ##
## If the credentials are not good, the user is redirected back to the index page with an 'invalid user' message ## 
@app.route('/_login', methods=['POST'])
def _login():
    try: #tries to get username and password
        user = request.form['user'].lower()
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
        session['theme'] = str(fetchers.get_theme(user))
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
    try: #checks if there is a theme stored in session to remember
        theme = session['theme']
    except KeyError:
        theme = "0"
    return render_template('signup.html', error = error, user = user, name = name, theme=theme)

### _signup helper route ###
## This helper page is accessed when info is entered from the signup page. ##
## It checks that the info is good, adds the info to the database, and redirects to the home page ##
@app.route('/_signup', methods = ['POST'])
def _signup():
    try: #tries to get info for form
        user = request.form["user"].lower()
        password = request.form["password"]
        passwordRepeat = request.form["passwordRepeat"]
        name = request.form["name"].strip()
    except KeyError: #only runs is someone messes with the html
        password, passwordRepeat, user, name = "", "", "", ""
    
    error = checks.check_for_signup_error(user, password, passwordRepeat, name)
    if error:
        session['error']=error
        session['user']=user
        session['name']=name
        return redirect(url_for('signup'))
    else:
        try:
            player=Player(
                user = user,
                password = hashing.hashpass(password),
                name = name,
                games = json.dumps([]),
                theme = 0,
                stats = json.dumps({"played": 0, "survivalWins": 0, "killWins": 0, "kills": 0}),
                status = ""
            )
            db.session.add(player)
            db.session.commit()
        except Exception as e:
            return(str(e))
        session['theme'] = "0"
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
    try: 
        foundPlayer = Player.query.filter_by(user = session['user']).first()
        data['name'] = foundPlayer.name
        data['status'] = foundPlayer.status
        data['theme'] = str(foundPlayer.theme)
        data['activeGames'], data['pastGames'] = [], []
        games = json.loads(foundPlayer.games)
        for game in games: #sorts games into active and past ones
            if checks.check_if_game_complete(game) == 'active':
                data['activeGames'].append(fetchers.get_active_button_info(game))
            else:
                data['pastGames'].append(fetchers.get_past_button_info(game))
        data['stats'] = json.loads(foundPlayer.stats)
    except Exception as e:
	    return(str(e))
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

    foundPlayer = Player.query.filter_by(user = session['user']).first()
    foundPlayer.name = name
    foundPlayer.status = status
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/_change_theme', methods = ['POST'])
def _change_theme():
    if not verifiers.verify_session_logged_in():
        session['error']="You cant access _change_theme page before logging in!"
        return redirect(url_for('index'))

    foundPlayer = Player.query.filter_by(user = session['user']).first()
    theme = foundPlayer.theme
    theme = (theme + 1)%4
    session['theme'] = str(theme)
    foundPlayer.theme = theme
    db.session.commit()
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
    theme = session['theme']
    return render_template('join.html', error = error, theme = theme)

### join helper route ###
@app.route('/_join/', methods = ['POST'])
def _join():
    if not verifiers.verify_session_logged_in():
        session['error']="You cant access _join page before logging in!"
        return redirect(url_for('index'))

    try: #tries to get code
        code = request.form['code'].lower()
    except KeyError: #only runs if someone messes with html
        code = ""

    error = checks.check_for_join_error(code)
    if error:
        session['error'] = error
        return redirect(url_for('join'))
    else:
        foundPlayer = Player.query.filter_by(user = session['user']).first()
        foundGame = Game.query.filter_by(user = code).first()
        foundGame.players = json.dumps(json.loads(foundGame.players)+[session['user']])#adds user to the player list of the game
        foundPlayer.games = json.dumps(json.loads(foundPlayer.games)+[code]) #adds game to the games list of the user
        db.session.commit()
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
    theme = session['theme']
    return render_template('create.html', error = error, code = code, name=name, theme = theme)

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
        code = request.form['code'].lower().strip()
        name = request.form['name'].strip()
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
        try:
            game=Game(
                code = code,
                name = name, 
                settings = json.dumps(settings), 
                host = session['user'], 
                started = 0, 
                players = json.dumps([session['user']]), 
                alive = json.dumps([]), 
                purged = json.dumps([]), 
                targets = json.dumps({}), 
                killCount = json.dumps({}), 
                killLog = json.dumps([])
            )
            db.session.add(game) #adds game to game table
            foundPlayer = Player.query.filter_by(user = session['user']).first()
            foundPlayer.games = json.dumps(json.loads(foundPlayer.games)+[code]) #adds game to the games list of the user
            db.session.commit()
        except Exception as e:
            return(str(e))
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
    foundGame = Game.query.filter_by(code = code).first()
    data['code'] = code
    data['user'] = session['user']
    data['title'] = foundGame.name
    data['admin'] = (foundGame.host == session['user'])
    data['started'] = foundGame.started
    data['settings'] = json.loads(foundGame.settings)
    data['host'] = foundGame.host
    data['theme'] = session['theme']
    data['players'] = []
    for player in  json.loads(foundGame.players):
        data['players'].append({'user': player, 'name': fetchers.get_name(player), 'status': fetchers.get_status(player)})
    data['numberOfPlayers'] = len(data['players'])
    data['alive'] = json.loads(foundGame.alive)
    data['purged'] = json.loads(foundGame.purged)
    if foundGame.started:
        data['word'] = json.loads(foundGame.targets)[session['user']]['word']
        data['target'] = json.loads(foundGame.targets)[session['user']]['target']
    data['isAlive'] = session['user'] in data['alive']

    return render_template('game.html', data = data, error=error)

### helper function for game. runs is the game is over ###
def pastGame(code):
    try:
        error = session.pop('error')
    except KeyError:
        error = ""
    data={}
    foundGame = PastGame.query.filter_by(code = code).first()
    data['code'] = code
    data['user'] = session['user']
    data['theme'] = session['theme']
    data['title'] = foundGame.name
    data['settings'] = json.loads(foundGame.settings)
    data['host'] = foundGame.host
    data['survivalWinner'] = {'code': foundGame.survivalWinner, 'name': fetchers.get_name(foundGame.survivalWinner)} #TODO: rename code to user 
    data['killWinners'] = [{'code': winner, 'name': fetchers.get_name(winner)} for winner in json.loads(foundGame.killWinners)]
    data['killLog'] = [{
        'method': entry[1],
        'victim': {'code': entry[2], 'name': fetchers.get_name(entry[2])}, 
        'assassin': {'code': entry[0], 'name': fetchers.get_name(entry[0])}, 
        'word': entry[3]
        } for entry in json.loads(foundGame.killLog)]
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
    foundGame = Game.query.filter_by(code = code).first()
    foundGame.started = 1
    foundGame.alive = foundGame.players
    players = json.loads(foundGame.players)
    settings = json.loads(foundGame.settings)
    targets = {}
    n=len(players)
    permutation = maff.random_permutation(n)
    for i in range(n):
        targets[players[permutation[i]]] = {"word": maff.get_word(settings), "target": players[permutation[(i+1)%n]], "assassin": players[permutation[i-1]]}
    targets = json.dumps(targets)
    killCount={}
    for player in players:
        killCount[player] = 0
    killCount = json.dumps(killCount)
    foundGame.targets = targets
    foundGame.killCount = killCount
    db.session.commit()
    return redirect(url_for('game', code = code))

@app.route('/_change_settings/<code>', methods = ['POST'])
def  _change_settings(code):
    if not verifiers.verify_session_logged_in():
        session['error']="You cant access _change_settings page before logging in!"
        return redirect(url_for('index'))

    if not verifiers.verify_host(code):
        return redirect(url_for('home'))

    settings = {}
    try: #tries to get info
        settings['difficulty'] = request.form['difficulty']
        settings['passon'] = request.form['passon']
    except KeyError: #this only runs is someone messes with the html
        settings['difficulty'], settings['passon'], = "", ""
    
    error = checks.check_for_settings_error(settings)
    if error:
        session['error'] = error
        return redirect(url_for('game', code = code))

    foundGame = Game.query.filter_by(code = code).first()
    foundGame.settings = json.dumps(settings)
    db.session.commit()
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
    
    foundGame = Game.query.filter_by(code = code).first()
    for player in foundGame.players: #delets the game from each players game list
        foundPlayer = Player.query.filter_by(user = player).first()
        games = json.loads(foundPlayer.games)
        games.remove(code) #removes game to the games list of the user
        foundPlayer.games = json.dumps(games) 
    db.session.delete(foundGame)
    db.session.commit()
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

    foundGame = Game.query.filter_by(code = code).first()
    foundPlayer = Player.query.filter_by(user = user).first()
    games = json.loads(foundPlayer.games)
    games.remove(code) #removes game from the games list of the user
    foundPlayer.games = json.dumps(games) 
    players = json.loads(foundGame.players)
    players.remove(user)  #removes user from the player list of the game
    foundGame.players = json.dumps(players) 
    db.session.commit()
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

    foundGame = Game.query.filter_by(code = code).first()
    alive = json.loads(foundGame.alive)
    alive.remove(user)  #removes user from the alive list of the game
    settings = json.loads(foundGame.settings)
    targets = maff.edit_targets_on_kill(user, json.loads(foundGame.targets), settings)
    killCount = json.loads(foundGame.killCount)
    killCount[targets[user]['assassin']] += 1 #adds to assassin's kill count
    killLog = json.loads(foundGame.killLog)+[(targets[user]['assassin'], "killed", user, targets[user]['word'])] #adds to kill log
    if len(alive) > 1: #if the game is not yet over
        foundGame.alive = json.dumps(alive)
        foundGame.targets = json.dumps(targets)
        foundGame.killCount = json.dumps(killCount)
        foundGame.killLog = json.dumps(killLog)
    else:  #the game has just finished
        players = json.loads(foundGame.players)
        survivalWinner = alive[0]
        killWinners = maff.create_killWinners(players, killCount)
        fetchers.distribute_kills_and_wins(players, killCount, survivalWinner, killWinners)
        pastgame=PastGame(
            code = code,
            name = foundGame.name, 
            settings = foundGame.settings, 
            host = foundGame.host, 
            players = json.dumps(players),
            survivalWinner = survivalWinner,
            killWinners = json.dumps(killWinners),
            killLog = json.dumps(killLog)
        )
        db.session.add(pastgame)
        db.session.delete(foundGame)#deletes from games
    db.session.commit()
    return redirect(url_for('game', code = code))

### purge page for purging a player by game host ###
@app.route('/_purge/<code>/<user>', methods = ['POST'])
def _purge(code, user):
    if not verifiers.verify_session_logged_in():
        session['error']="You cant access _purge page before logging in!"
        return redirect(url_for('index'))
    #TODO: check if page is updated with database. Catches if host tries purging without refreshing page
    if not verifiers.verify_host(code):
        session['error']="something is not right! (_purge)"
        return redirect(url_for('game', code = code))

    error = checks.check_for_purge_error(code, user)
    if error:
        session['error'] = error
        return redirect(url_for('game', code = code))
    
    foundGame = Game.query.filter_by(code = code).first()
    alive = json.loads(foundGame.alive)
    alive.remove(user)  #removes user from the alive list of the game
    settings = json.loads(foundGame.settings)
    targets = maff.edit_targets_on_kill(user, json.loads(foundGame.targets), settings)
    killCount = json.loads(foundGame.killCount)
    killLog = json.loads(foundGame.killLog)+[(targets[user]['assassin'], "purged", user, targets[user]['word'])] #adds to kill log
    purged = json.loads(foundGame.purged)+[user] #adds user to the purged list of the game
    if len(alive) > 1:
        foundGame.alive = json.dumps(alive)
        foundGame.targets = json.dumps(targets)
        foundGame.killLog = json.dumps(killLog)
        foundGame.purged = json.dumps(purged)
    else:
        players = json.loads(foundGame.players)
        survivalWinner = alive[0]
        killWinners = maff.create_killWinners(players, killCount)
        fetchers.distribute_kills_and_wins(players, killCount, survivalWinner, killWinners)
        pastgame=PastGame(
            code = code,
            name = foundGame.name, 
            settings = foundGame.settings, 
            host = foundGame.host, 
            players = json.dumps(players),
            survivalWinner = survivalWinner,
            killWinners = json.dumps(killWinners),
            killLog = json.dumps(killLog)
        )
        db.session.add(pastgame)
        db.session.delete(foundGame)#deletes from games
    db.session.commit()
    return redirect(url_for('game', code = code))

@app.route('/rules/')
def rules():
    try:
        theme = session['theme']
    except KeyError:
        theme = "0"
    return render_template('rules.html', theme=theme)

#### 404 ROUTING BELOW THIS LINE ####
@app.route('/<path>/')



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