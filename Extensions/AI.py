'''
Created on Jun 9, 2012
@author: Nisheeth
'''

import re
import random
import urllib2
import urllib
import hashlib
import cookielib
from Util.Log import Log
from Util import htmlx
from Util.redict import redict


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
                                                            #"Ask your mom, $u", 
                                                            "I AM YOUR FAAATHAAA!!", 
                                                            "I'd rather not say, $u", 
                                                            "If I tell you I'd have to kill you, $u",
                                                            #"Who the fuck are YOU to ask me who I am?",
                                                            "I am Batman, you jelly?",
                                                            #"The one who ass raped you in your sleep last night.",
                                                            "I am Qircky.",
                                                            "Your worst nightmare."
                                                        ]
        self._redict[(r'\b(hi|hello|sup|holla|hey)\b', re.I)] = [
                                                                    "I'm good, you feeling better?, $u",
                                                                    "Hi, $u",
                                                                    "WASSSSUP! $u",
                                                                    "Hey $u.",
                                                                    "Morning...wait...Evening...eh..Fuck this shit, I'm out",
                                                                    "Peace nigga",
                                                                    "Glory to Earth"
                                                                ]
        self._redict[(r'\bhow (are|r) (you|u)\b', re.I)] = [
                                                                    #"I'm good, your butt feeling any better?, $u",
                                                                    "Fine, I guess",
                                                                    "I'm good, $u",
                                                                    "Get lost punk."
                                                                ]
        self._redict[(r'\bhow do (you|u) do\b', re.I)] = [
                                                                    #"Do what asshole?",
                                                                    #"First I get naked, put on a condom then I fuck your ass.",
                                                                    "Doggy Style.",
                                                                    "Missionary.",
                                                                    "Wheelbarrow."
                                                                ]
        self._redict[(r'\b(?:arm|activate) (.*)', re.I)] = [
                                                    "Powering up $1 for $u", 
                                                    "No you activate that shit yourself, $u",
                                                    "$1: All Systems Online.",
                                                    "Piss off Nazi.",
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
        
    def reply(self, stimuli, user):
        '''
            @param stimuli: An input trigger
            @param user: The user asking the bot
            @summary: Returns a reply given an input stimuli
            @return: str, Reply
        '''
        for (k,v) in self._redict.iter_regex():     # Match for the stimuli
            m = k.search(stimuli)
            if m is not None:
                return self.think(stimuli, m, v, user)  # Think and return a response   
    
    def think(self, stimuli, m, v, user):
        '''
            @param stimuli: An input trigger
            @param m: The match object for substituting backreferences
            @param v: The possible responses
            @param user: The user asking the bot
            @summary: Returns a reply given an input stimuli
            @return: str, Reply
        '''        
        s = iter(v[random.randrange(0, len(v))])        # Get a random response
       
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
        return None if reply == "" else reply
    
    
class CleverBot(object):
    '''
        CleverBot handles the interaction between the bot by replying using cleverbot.com 
    '''
    def __init__(self, config=None):
        self.params = {
                    'url'       : 'http://www.cleverbot.com/webservicemin',
                    'name'      : 'Bot'
                }
        if config:
            self.params.update(config)
            
        self.data = {
                 'stimulus'         : '',
                 'start'            : '',
                 'sessionid'        : '',
                 'vText8'           : '',
                 'vText7'           : '',
                 'vText6'           : '',
                 'vText5'           : '',
                 'vText4'           : '',
                 'vText3'           : '',
                 'vText2'           : '',
                 'icognoid'         : 'wsf',
                 'icognocheck'      : '',
                 'fno'              : '0',
                 'prevref'          : '',
                 'emotionaloutput'  : '',
                 'emotionalhistory' : '',
                 'asbotname'        : 'Bot',
                 'ttsvoice'         : '',
                 'typing'           : '',
                 'lineref'          : '',                 
                 'sub'              : 'Say',
                 'islearning'       : '1',
                 'cleanslate'       : 'false'
            }
        self.headers = {
                    'User-Agent'        : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:7.0.1) Gecko/20100101 Firefox/7.0',
                    'Accept'            : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language'   : 'en-us;q=0.8,en;q=0.5',
                    'X-Moz'             : 'prefetch',
                    'Accept-Charset'    : 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                    'Referer'           : 'http://www.cleverbot.com',
                    'Cache-Control'     : 'no-cache',
                    'Pragma'            : 'no-cache'
                }
        self.response_keys = [
                      'message',
                      'sessionid',
                      'logurl',
                      'vText8',
                      'vText7',
                      'vText6',
                      'vText5',
                      'vText4',
                      'vText3',
                      'vText2',
                      'prevref',
                      '__unused__',
                      'emotionalhistory',
                      'ttsLocMP3',
                      'ttsLocTXT',
                      'ttsLocTXT3',
                      'ttsText',
                      'lineref',
                      'lineURL',
                      'linePOST',
                      'lineChoices',
                      'lineChoicesAbbrev',
                      'typingData',
                      'divert',
                ]
        self.response = {}
        self.connect()
    
    def connect(self):
        cj = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
                
    def ask(self, msg):
        try:
            self.data['stimulus'] = msg        
            self.data['icognocheck'] = self.query_hash(self.data)            
            req = urllib2.Request(self.params['url'], urllib.urlencode(self.data), self.headers)
            resp = self.opener.open(req)
            msg = resp.read()
            resp.close()
            return self.parse_response(msg)
        except Exception:
            Log.error()
            return None                    
                
    def parse_response(self, resp):                       
        for k,v in zip(self.response_keys, resp.split("\r")):
            try:
                self.response[k] = v
                if self.data.has_key(k):
                    self.data[k] = v
            except:
                pass
        return htmlx.unescape(self.response['ttsText'])
        
    def query_hash(self, params):
        query = urllib.urlencode(params)[9:29]
        return hashlib.md5(query).hexdigest()
        