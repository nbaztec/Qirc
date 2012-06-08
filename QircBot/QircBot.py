'''
Created on Jun 7, 2012

@author: Nisheeth
'''

import socket
import random
import time
import re
from PseudoIntelligence import PseudoIntelligence
from threading import Thread, Lock
from Extensions import Search

class QircBot(object):
    '''
        QircBot manages the working of the bot as well as the interface
    '''
    
    re_name = re.compile(r'^:([^!]+)!')    
    
    def __init__(self, callback, params=None):
        '''
            @var callback  : A callback function to be called when bot is successfully registered
            @var params    : Parameters for the bot,
                             Default:
                                  'host'        : 'irc.freenode.net'
                                  'port'        : 6667
                                  'nick'        : 'QircBot'
                                  'ident'       : 'QircBot'
                                  'realname'    : 'QirckyBot'  
                                  'password'    : None                             
        '''
        
        self.params = {
              'host'        : 'irc.freenode.net',
              'port'        : 6667,
              'nick'        : 'QircBot',
              'ident'       : 'QircBot',
              'realname'    : 'QirckyBot',
              'password'    : 'None'                  
              }
        if params is not None:            
            self.params.update(params)
            
        print self.params
        self._sock = socket.socket();
        self._retry_timeout = 15    # 15 seconds connection retry
        self._callback = callback     
        self.lock = Lock()          # mutex lock       
        self._intelli = PseudoIntelligence()    # AI module, Work in development          
        self.orig_nick = self.params['nick']    # Store original nick for temp logins
        self._arma_whitelist = ['nbaztec', 'QircBot']
    
    def connect(self):
        '''
            @summary: Tries to connec to the IRC Server. Retries after exponential time.
        '''                                
        try:
            self._sock.connect((self.params['host'], self.params['port']))            
            self._retry_timeout = 15
            return True
        except Exception, e:
            print 'Failed to connect', e, 'Reconnecting in', self._retry_timeout, 'seconds'
            time.sleep(self._retry_timeout)
            self._retry_timeout *= 0.5               
        pass
    
    def register(self):
        '''
            @summary: Registers the bot on IRC
        '''
        self._ghost = False
        self.send("NICK %s" % self.params['nick'])
        self.send("USER %s %s bla :%s" % (self.params['ident'], self.params['host'], self.params['realname']))        
        pass
    
    def send(self, msg):
        '''
            @var msg: Message to send
            @summary: Send raw message to IRC
        '''
        print 'Sending', msg
        self._sock.send(msg + "\r\n")        
            
    def begin_read(self):
        '''
            @summary: Launches an async thread for reading
        '''
        self._read_thread = Thread(target=self.read)
        self._read_thread.start()
        
    def read(self):
        '''
            @summary: Synchronous reading via polling 
        '''
        try:
            self._read_buffer = ''
            run_read = True
            while run_read:
                self.last_read = time.time()        # Last read time
                self._read_buffer = self._read_buffer + self._sock.recv(2048)
                temp = str.split(self._read_buffer, "\n")
                self._read_buffer = temp.pop()            
                run_read = self.parse_msg(temp)     # Dispatch message for parsing
        except:
            pass
        print "Boom! Owww. *Dead*"
            
    def done_read(self, seconds):        
        '''
            @summary: Checks if x seconds have elapsed since the last read
        '''
        return (time.time() - self.last_read) < seconds
                
    def join(self, chan):
        '''
            @var chan: The channel to join. Example #chan
            @summary: Sends a JOIN command to join the channel and updates the current channel
        '''
        self.params.update({'chan': chan})                
        self.send("JOIN "+chan)
        
    def identify(self):
        '''
            @summary: Sends a message to identify bot's NICK 
        '''
        self.send("PRIVMSG nickserv :identify %s" % self.params['password'])
        
    def ghost(self, nick):
        '''
            @var nick: NICK to ghost
            @summary: Sends a message to NickServ to ghost a NICK
        '''
        self.send("PRIVMSG nickserv :ghost %s %s" % (nick, self.params['password']))
    
    def nick(self, nick):
        '''
            @var nick: New nick for bot
            @summary: Sends a NICK message to to change bot's nick
        '''
        self.send("NICK %s" % nick)    
        
    def disconnect(self, msg):
        '''
            @var msg: QUIT message
            @summary: Disconnect the bot from the IRC
        '''
        self.send('QUIT :%s' % msg)         
    
    def say(self, msg):     
        '''
            @var msg: Message to say
            @summary: Say something in the current channel
        '''   
        self.send('PRIVMSG %s :%s' % (self.params['chan'], msg))
        
    def msg(self, nick, msg):
        '''
            @var nick: User nick or channel
            @var msg: Message to say
            @summary: Say something to a channel or user
        '''   
        self.send('PRIVMSG %s :%s' % (nick, msg))
    
    def kick(self, nick, msg):        
        '''
            @var nick: User nick
            @var msg: KICK reason
            @summary: Kicks a user from the channel
            @attention: Requires OP mode
        '''
        self.send('KICK %s %s %s' % (self.params['chan'], nick, ' :'+msg if msg else ''))
    
    def ban(self, host, reason):
        '''
            @var host: User's hostmask
            @var reason: KICK reason
            @summary: Bans a user from the channel
            @attention: Requires OP mode
        '''    
        self.send('MODE %s +b %s %s' % (self.params['chan'], host, reason))
        pass
    
    def unban(self, host):    
        '''
            @var host: User's hostmask
            @summary: Unbans a user from the channel
            @attention: Requires OP mode
        ''' 
        self.send('MODE %s -b %s' % (self.params['chan'], host))
        pass
    
    def names(self): 
        '''
            @summary: Send a NAME command to get the list of usernames in the current channel
        '''       
        self.send('NAMES %s' % self.params['chan'])        
    
    def action(self, msg):
        '''
            @var msg: Message to display
            @summary: Send an ACTION message
        '''
        self.send("PRIVMSG %s :\x01ACTION %s\x01" % (self.params['chan'], msg))
    
    # WARNING: Do you know what you are doing?
    def armageddon(self, build=False):  
        '''
            @var build: True if called for first time, from stage 0. False otherwise.
            @summary: Does what it says. Armageddon.
                      Kickbans all users except the ones in whitelist
        '''      
        if build and self._armastep == 0:               # Stage 1, Prepare usernames
            self._armastep += 1
            self.names()
        elif self._armastep == 1:                       # Stage 2, Prepare userhosts
            self._armastep += 1            
            self.send("USERHOST %s" % ' '.join(self.usernames))
        elif self._armastep == 2:                       # Stage 3, Get +o mode {optional}
            self._armastep += 1            
            #self.send("PRIVMSG ChanServ :op %s %s" % (self.params['chan'], self.params['nick']))
            Thread(target=self.armageddon).start()  
        else:                                           # Final Stage, kickban everyone except in whitelist
            self._armastep = 0                          # Reset armageddon to Stage 0
            for u,h in self.userhosts.iteritems():                            
                if re.match(r'^~(%s)' % '|'.join(self._arma_whitelist), h) is None:                                        
                    print 'armageddon-kickban', u, h
                    self.ban('*!' + h, 'ARMAGEDDON')
                    self.kick(u, 'ARMAGEDDON')                                
        
    # Big Guns
    
    def parse_msg(self, msg):
        '''
            @var msg: Message from IRC
            @summary: Parses the messages coming from the IRC to take suitable actions
        '''
        for line in msg:
            line=str.rstrip(line)   # Strip '\r' characters if present
            line=str.split(line) 
            print ' '.join(line)    # Print line
                       
            # Important Messages
            if(line[0] == "PING"):                          # PING/PONG : Must reply to this
                self.send("PONG %s" % line[1]) 
            elif(line[1] == "QUIT" or line[1] == "PART"):   # QUIT/PART
                m = QircBot.re_name.match(line[0])          # Get name of the parting user
                user = m.group(1)
                if user == self.params['nick']:
                    return False
                else:
                    self.say('Bye bye ' + user)
            elif(line[1] == "JOIN"):                        # JOIN
                m = QircBot.re_name.match(line[0])          # Get name of the joining user
                user = m.group(1)
                if user == self.params['nick']:
                    self.say('All systems go!')
                else:
                    self.say('Hey ' + user)
            elif(line[1] == "KICK"):                        # KICK
                self.join(self.params['chan'])
            elif(line[1] == "NOTICE"):                      # NOTICE
                if ' '.join(line[3:]).find(' has been ghosted') != -1:  # Duplicate NICK has been ghosted
                    self.nick(self.orig_nick)                           # Claim original NICK
                    self.identify()                                     # Identify
            elif(line[1] == "NICK"):                        # NICK
                m = self.re_name.search(line[0]);           # Update nick when changed
                if m.group(1) == self.params['nick']:
                    self.params['nick'] = ' '.join(line[2:]).strip(':@+')     
            
            # Control Messages
            if line[1] == "433":                            # NICK already in use                
                self.params['nick'] += str(random.randrange(1,65535)) 
                print 'Retrying with nick', self.params['nick']
                self._ghost = self.params['password'] is not None   # Ghost other user/bot if password is specified
                self.register()                                     # Retry registering
            elif line[1] == "376":                          # End of /MOTD command
                if self._ghost:                             # If ghosting requested
                    self.ghost(self.orig_nick)                    
                    self._ghost = False
                else:
                    self.identify()                         # Normal join, just identify
                self.usernames = []                         # Init usernames
                self._armastep = 0                          # Init armageddon stage to 0
                Thread(target=self._callback, args=(self,)).start() # Call callback function
            elif line[1] == "353":                          # NAMES
                self.usernames = [x.strip(':@+') for x in line[5:]] # Get clean names
            elif line[1] == "366":                          # End of /NAMES list
                print "Usernames", self.usernames                                
                if self._armastep == 1:                    
                    Thread(target=self.armageddon).start()                
            elif line[1] == "302":                          # USERHOST
                if self._armastep == 3:                    
                    self.userhosts = {}  
                    for uh in line[3:]:                     # Build userhosts
                        m = re.search(r'([^=]*)=\+(.*$)', uh)
                        self.userhosts[m.group(1).strip(':@+')] = m.group(2)                                 
                    Thread(target=self.armageddon).start()
                    print "Userhosts", self.userhosts                
                        
            # Fun Messages
            elif line[1] == "PRIVMSG":                  
                m = QircBot.re_name.match(line[0])          # If message is a channel message or private message for bot
                if m:                                       # Call extended parser in separate thread
                    Thread(target=self.extended_parse, args=(m.group(1), str.lstrip(' '.join(line[3:]),':'),)).start()                                            
        return True
    
    def parse_cmd(self, cmd):
        '''
            @var cmd: Command from standard input
            @summary: Parses the command from standard input to take suitable actions
        '''        
        if cmd.startswith('quit'):
            if len(cmd) > 5:
                self.disconnect(cmd[5:])
            else:
                self.disconnect("I'll be back.")
            return False
        elif cmd.startswith('say '):
            self.say(cmd[4:])
        elif cmd.startswith('join '):
            self.join(cmd[5:])
        elif cmd.startswith('me '):
            self.action(cmd[3:])
        elif cmd.startswith('msg '):
            self.msg(cmd[4:])
        elif cmd.startswith('kick '):
            self.kick(cmd[5:], cmd[5:])
        elif cmd.startswith('ban '):
            m = re.search(r'ban ([\w\d|]+)( (.*))?', cmd)
            if m.group(2):
                self.ban(m.group(1), m.group(2))
            else:
                self.ban(m.group(1), m.group(1))                    
        elif cmd.startswith('unban '):
            m = re.search(r'unban ([\w\d|]+)( (.*))?', cmd)
            if m.group(2):
                self.unban(m.group(1))
            else:
                self.unban(m.group(1))
        elif cmd.startswith('armageddon'):
            self.armageddon(build=True)
        else:
            self.send(cmd)
        return True
                
    def extended_parse(self, user, msg):        
        '''
            @var user: The sender's nick
            @var msg: Message for bot
        '''
        print msg                            
        # Commands
        r = None
        exec_cmd = True
        if msg.startswith('!wiki'):            
            r = Search.wiki(msg[6:])                    
        elif msg.startswith('!wolf'):
            r = Search.wolfram(msg[6:])                        
        elif msg.startswith('!g'):
            r = Search.google(msg[3:])                        
        elif msg.startswith('!tdf'):
            r = Search.tdf(msg[5:])
        else:
            exec_cmd = False
            if re.search(r'\b' + self.params['nick'] + r'\b', msg):     # If bot's name is present            
                self.say(self._intelli.reply(msg, user))                # Use AI for replying                
            
        # Say if some output was returned
        if r is not None:
            self.say(user+', '+r)
        elif exec_cmd:
            self.say("No results for you %s." % user)