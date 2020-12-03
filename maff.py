import math, numpy

### modifies the targets map after user is killed ###
def edit_targets_on_kill(user, targets):
    targets[targets[user]['assassin']]['word'], targets[user]['word'] = targets[user]['word'], targets[targets[user]['assassin']]['word'] #swaps words with the assassin
    targets[targets[user]['assassin']]['target'] = targets[user]['target'] #changes assassin's target
    targets[targets[user]['target']]['assassin'] = targets[user]['assassin'] #changes target's assassin
    targets[user]['target'] = targets[user]['assassin'] #sets target to assassin
    return targets

#returns a random permutation of the numbers 0 through n-1
def random_permutation(n):
    return numpy.random.permutation(n)
    #TODO: implement this function without using numpy