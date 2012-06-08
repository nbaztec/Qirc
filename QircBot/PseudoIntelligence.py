'''
Created on Jun 8, 2012

@author: Nisheeth
'''
from Util.redict import redict
import re
import random

class PseudoIntelligence(object):
    '''
        @summary: A simple class to act as an AI for bot
    '''
    def __init__(self):
        self._redict = redict()
        self.build()
        
    def build(self):
        '''
            @summary: Build the rules for AI
        '''
        self._redict[(r'who (are|r) (you|u)', re.I)] = [
                                                            "Ask your mom, $u", 
                                                            "I AM YOUR FAAATHAAA!!", 
                                                            "I'd rather not say, $u", 
                                                            "If I tell you I'd have to kill you, $u",
                                                            "Who the fuck are YOU to ask me who I am?",
                                                            "I am Batman, you jelly?",
                                                            "The one who ass raped you in your sleep last night.",
                                                            "I am Qircky.",
                                                            "Your worst nightmare, bitch."
                                                        ]
        self._redict[(r'\b(hi|hello|sup|holla|hey)\b', re.I)] = [
                                                                    "I'm good, your butt feeling better?, $u",
                                                                    "Hi, $u",
                                                                    "WASSSSUP! $u",
                                                                    "Hey fuckface.",
                                                                    "Morning...wait...Evening...eh..Fuck this shit, I'm out",
                                                                    "Peace nigga",
                                                                    "Glory to Earth"
                                                                ]
        self._redict[(r'\bhow (are|r) (you|u)\b', re.I)] = [
                                                                    "I'm good, your butt feeling any better?, $u",
                                                                    "Fine, assface",
                                                                    "I'm good, $u",
                                                                    "Just fuck off. _|_"
                                                                ]
        self._redict[(r'\bhow do (you|u) do\b', re.I)] = [
                                                                    "Do what asshole?",
                                                                    "First I get naked, put on a condom then I fuck your ass.",
                                                                    "Doggy Style."
                                                                ]
        self._redict[(r'\barm|activate (.*)', re.I)] = [
                                                    "Powering up $1 for $u", 
                                                    "No you activate that shit yourself, $u",
                                                    "$1: All Systems Online.",
                                                    "Fuck off Nazi.",
                                                    "Arming $1 for Mein Fuhrer.",
                                                    "Activating $1 for $u."
                                                ]
        self._redict[(r'\bfire at ([\w\d]+)', re.I)] = [
                                                    "Firing at $1. PIIKAACHUUUUUU!!!", 
                                                    "Ok $u, here goes nothing. KABOOM!",
                                                    "$1, you're dead meat. *BOOM*",
                                                    "Yes Mein Fuhrer. *POOF*",
                                                    "Sir yes sir. WARRR!!"
                                                ]
        self._redict[(r'\bneed\b.*\bmoney\b', re.I)] = [
                                                    "Get lost beggar.", 
                                                    "Ok $u, accept my generous donation of _|_",
                                                    "Yawn, wipe my feet first $u.",
                                                    "And I need sex.",
                                                    "Money doesn't grow on trees faggot",
                                                    "One doesn't simply GET money, noob."
                                                ]
        self._redict[(r'.*', re.I)] = [
                                           "Fuck off, $u",
                                           "Get lost, $u",
                                           "OMG! LOL! LMAO! YOLO! You're so 1337, asshole -_-",
                                       ]
        
    def reply(self, stimuli, user):
        '''
            @var stimuli: An input trigger
            @var user: The user asking the bot
            @summary: Returns a reply given an input stimuli
            @return: str, Reply
        '''
        for (k,v) in self._redict.iter_regex():     # Match for the stimuli
            m = k.search(stimuli)
            if m is not None:
                return self.think(stimuli, m, v, user)  # Think and return a response   
    
    def think(self, stimuli, m, v, user):
        '''
            @var stimuli: An input trigger
            @var m: The match object for substituting backreferences
            @var v: The possible responses
            @var user: The user asking the bot
            @summary: Returns a reply given an input stimuli
            @return: str, Reply
        '''        
        s = iter(v[random.randrange(0, len(v))])        # Get a random response
        print s
        
        # Replace placeholders in template
        reply = ""
        for c in s:
            if c == "$":                            
                try:
                    c = s.next()
                    if c == "u":
                        reply += user
                    elif c.isdigit():
                        reply += m.group(int(c))
                except:
                    reply += c                                  
            else:
                reply += c                
        return reply
    
        