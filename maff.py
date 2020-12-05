#### This file contains helper functions that are computational and do not require many external packages ####
import random, os

### modifies the targets map after user is killed ###
def edit_targets_on_kill(user, targets):
    targets[targets[user]['assassin']]['word'], targets[user]['word'] = targets[user]['word'], targets[targets[user]['assassin']]['word'] #swaps words with the assassin
    targets[targets[user]['assassin']]['target'] = targets[user]['target'] #changes assassin's target
    targets[targets[user]['target']]['assassin'] = targets[user]['assassin'] #changes target's assassin
    targets[user]['target'] = targets[user]['assassin'] #sets target to assassin
    return targets

### generates the killWinners list for a game that has just completed ###
def create_killWinners(players, killCount):
    killWinners = []
    _max_kill_count = 0
    for player in players:
        if killCount[player] == _max_kill_count:
            killWinners.append(player)
        if killCount[player] > _max_kill_count:
            killWinners = [player]
            _max_kill_count = killCount[player]
    return killWinners

### returns a random permutation of the numbers 0 through n-1 ###
def random_permutation(n):
    ordered = []
    for i in range(0, n):
        ordered.append(i)
    random.shuffle(ordered)
    return ordered
 
### returns a random word out of the word bank (according to the settings) ###
def get_word(settings):
    basedir = os.path.abspath(os.path.dirname(__file__))
    fname = os.path.join(basedir, 'static/words/'+settings['difficulty']+'.txt')
    with open(fname, "r") as file:
        lines = file.read().splitlines()
    return random.choice(lines)