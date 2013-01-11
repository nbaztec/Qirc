'''
Created on Jun 10, 2012
@author: Nisheeth
'''

from threading import Thread
import time
#import math
import random
from Util.Log import Log
 
class Werewolf(object):
    '''
        @summary: Werewolf is a classic game where in a village is inhabited by a werewolves. The game is divided into day/night cycles. 
                  The werewolves devour a villager at night. During the day, the villagers vote to lynch the suspected werewolves.
                  The game ends when the number of villagers equals the number of werewolves or each werewolf is eliminated 
    '''

    def __init__(self, callback, pm):
        '''
            @param callback: The callback to the say function
            @param pm      : The callback to the notice/pm function            
        '''
        self.callback = callback   
        self.pm = pm     
        self._is_running = []             # Game is running
        self._is_joining = []             # Game in joining stage
        self._is_playing = []             # Game in playing stage
        self.time_of_day = 1                # 0: Day, 1: Night 
    
    def is_running(self, channel):
        return channel in self._is_running
    
    def is_joining(self, channel):
        return channel in self._is_joining
    
    def is_playing(self, channel):
        return channel in self._is_playing
        
    def start(self, channel):
        '''
            @summary: Start the game
        '''
        if self.is_running(channel):                 # Return if the game is already running
            return None
        
        self.users = {}                     # Build fresh list of players
        Thread(target=self.joining_period, name='joining_period').start()
        return "Starting Werewolf in 20s, type '+' to join in."
      
    def join(self, channel, user):
        '''
            @param user: The player's name
        '''
        if self.is_joining and user not in self.users:            
            self.users[user] = 0            # 0: Human, 1: Wolf
            Thread(target=self.pm, args=(user, 'Welcome %s.' % user,), name='pm').start()
        
    def joining_period(self, channel):
        '''
            @summary: Calls the timeout of joining period
        '''
        self.is_running = True
        self.is_joining = True        
        time.sleep(20)                      # 20 seconds timeout
        self.is_joining = False
        self.assign()                       # Assign roles to players
        
    def assign(self, channel):
        '''
            @summary: Assigns the roles to players; 0 for Human, 1 for Werewolf. Then starts the game
        '''
        total_count = len(self.users)       # Total players
        if total_count < 4:                 # Minimum players, Recommended: 4
            Thread(target=self.callback, args=('Sorry minimum of 4 players are required to play this game. Call your friends!',)).start()
            self.is_running = False         # Game ended
        else:            
            self.wolves = 1                                 # Werewolf count, Recommended: math.ceil(total_count/5)
            users = self.users.keys()                   
            random.shuffle(users)                           # Shuffle players
            i = 0
            for k in users:                                 # First `self.wolves` users are made werewolves
                if i == self.wolves:                        # Rest everyone is made a villager
                    Thread(target=self.pm, args=(k, 'You are a villager %s. Trod carefully.' % k,), name='pm').start()
                else:
                    self.users[k] = 1   # Werewolf
                    i += 1
                    Thread(target=self.pm, args=(k, 'You are a werewolf %s. Eat them all!' % k,), name='pm').start()
            self.villagers = total_count - self.wolves      # Number of villagers
            #Thread(target=self.callback, args=('There is a werewolf amidst %s. Good luck!' % (were_count, ', '.join(self.users.keys())),), name='callback').start()
            Thread(target=self.callback, args=('There is a werewolf amidst %s. Good luck!' % ', '.join(self.users.keys()),), name='callback').start()
            Thread(target=self.game, name='game').start()
              
    def lynch(self, channel, user, vote):     
        '''
            @param user: The name of the player
            @param vote: The name of the suspected player
            @summary: Registers votes of players
        '''           
        users = self.users.keys()                       
        if self.time_of_day == 0:                       # Vote only during day
            if user in users:                           # If user is playing
                if vote in users and user in users:     # If suspect is in igame
                    if self.lynch_vote.has_key(vote):   # Register vote
                        self.lynch_vote[vote] += 1
                    else:
                        self.lynch_vote[vote] = 1
                else:
                    Thread(target=self.callback, args=("%s, no such player here named '%s'" % (user, vote),), name="callback").start()
            else:
                Thread(target=self.pm, args=(user, "%s, you are not in the game anymore" % user,), name="callback").start()
        else:
            Thread(target=self.callback, args=("%s, justice is not served at night you moron!" % user,), name="callback").start()
                
    def lynch_player(self, channel):
        '''
            @summary: Lynches the top suspected player
        '''
        m = 0                                   
        p = None                    
        for k,v in self.lynch_vote.items():     # Get top voted player
            if v > m:
                p = k
                m = v        
        if p:
            v = self.users.pop(p)               # Remove from game
            Log.write(self.users)
            if v:
                self.wolves -= 1
                Thread(target=self.callback, args=('%s was lynched! Justice is served. %s is dead.' % (p, p),), name='callback').start()
            else:
                self.villagers -= 1
                Thread(target=self.callback, args=('%s was lynched! Sinners all of you! The blood of innocent %s is on your hands.' % (p, p),), name='callback').start()
        else:      
            Thread(target=self.callback, args=("Come forth people, else the beast shall devour you all!",), name='callback').start()
    
    def choose_victim(self, channel):
        '''
            @summary: Randomly chooses a villager as the victim
            @return: victim, end_game|bool 
        '''
        r  = random.randrange(0, self.villagers)        # Get a random number from 0 to len(villager)-1
        i = 0
        victim = None
        for k,v in self.users.items():                  # Select the nth villager as victim
            if v == 0:
                if i == r:
                    victim = k
                    break
                else:
                    i += 1
                           
        self.users.pop(victim)                          # Remove from game
        self.villagers -= 1                         
        return victim, self.villagers == 0    # Is the number of wolves equal to the number or villagers?
         
    def game(self, channel):        
        self.is_playing = True                          # Start playing
        time.sleep(5)                                   # Customary delay
        while self.wolves and self.villagers:           # While one of any isn't dead 
            self.time_of_day = 1                        # Night time!
            Thread(target=self.callback, args=('Night Time! The beast hunts. Say your prayers everyone.',), name='callback').start()
            victim, is_last = self.choose_victim()                
            time.sleep(10)
            if is_last:
                Thread(target=self.callback, args=("Day Time! %s was eaten last night." % victim,), name='callback').start()
            if self.villagers == self.wolves:
                self.villagers = 0
                Thread(target=self.callback, args=("Day Time! %s was eaten last night." % victim,), name='callback').start()
                Thread(target=self.callback, args=("The lone survivor %s is outmatched by the werewolf. He flees." % victim,), name='callback').start()
            else:
                self.time_of_day = 0                    # Day time!
                self.lynch_vote = {}
                Thread(target=self.callback, args=("Day Time! %s was eaten last night. Time for justice. Identify the werewolf as '+ <nick>'" % victim,), name='callback').start()                            
                time.sleep(30)                          # Lynch tim!
                self.lynch_player()
                time.sleep(10)                          # Wait for night to descend
        # Game end
        self.is_playing = False
        self.is_running = False
        if self.wolves:         # If wolves remaining, they win
            Thread(target=self.callback, args=('The werewolf enjoyed the human buffet!',), name='callback').start()
        else:                   # If villagers remaining, they win
            Thread(target=self.callback, args=('The villagers killed the monster, hi5!',), name='callback').start()
    
        