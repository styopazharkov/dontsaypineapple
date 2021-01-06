from app import db

class Player(db.Model):
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(), nullable=False)
    password = db.Column(db.String(), nullable=False)
    name = db.Column(db.String(), nullable=False)
    games = db.Column(db.String(), nullable=False)
    theme = db.Column(db.Integer, nullable=False)
    stats = db.Column(db.String(), nullable=False)
    status = db.Column(db.String(), nullable=False)

    def __init__(self, user, password, name, games, theme, stats, status):
        self.user = user
        self.password = password
        self.name = name
        self.games = games
        self.theme =theme
        self.stats = stats
        self.status = status

    def __repr__(self):
        return '<id {}>'.format(self.id)
    

class Game(db.Model):
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(), nullable=False)
    name = db.Column(db.String(), nullable=False)
    settings = db.Column(db.String(), nullable=False)
    host = db.Column(db.String(), nullable=False)
    started = db.Column(db.Boolean, nullable=False)
    players = db.Column(db.String(), nullable=False)
    alive = db.Column(db.String(), nullable=False)
    purged = db.Column(db.String(), nullable=False)
    targets = db.Column(db.String(), nullable=False)
    killCount = db.Column(db.String(), nullable=False)
    killLog = db.Column(db.String(), nullable=False)

    def __init__(self, code, name, settings, host, started, players, alive, purged, targets, killCount, killLog):
        self.code = code
        self.name = name
        self.settings = settings
        self.host = host
        self.started = started
        self.players = players
        self.alive = alive
        self.purged = purged
        self.targets = targets
        self.killCount = killCount
        self.killLog = killLog


    def __repr__(self):
        return '<id {}>'.format(self.id)
    # def serialize(self):
    #     return {
    #         'id': self.id, 
    #         'name': self.name,
    #         'author': self.author,
    #         'published':self.published
    #     }

class PastGame(db.Model):
    __tablename__ = 'pastgames'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(), nullable=False)
    name = db.Column(db.String(), nullable=False)
    settings = db.Column(db.String(), nullable=False)
    host = db.Column(db.String(), nullable=False)
    players = db.Column(db.String(), nullable=False)
    survivalWinner = db.Column(db.String(), nullable=False)
    killWinner = db.Column(db.String(), nullable=False)
    killLog = db.Column(db.String(), nullable=False)

    def __init__(self, code, name, settings, host, players, survivalWinner, killWinner, killLog):
        self.code = code
        self.name = name
        self.settings = settings
        self.host = host
        self.players = players
        self.survivalWinner = survivalWinner
        self.killWinner = killWinner
        self.killLog = killLog


    def __repr__(self):
        return '<id {}>'.format(self.id)