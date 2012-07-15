'''
Created on Jun 7, 2012
@author: Nisheeth
@version: 3.0 Deadpool
'''

from Extensions import Search, Calc, Weather, Define, Locate, Url, Roll
from Extensions.Game import Werewolf
from Extensions.User import Tell, Seen, Remind  
from Extensions.CleverBot import CleverBot
from Extensions.VoteMaster import VoteMaster
from PseudoIntelligence import PseudoIntelligence
from QircOptionParser import QircOptionParser
from QircDatabase import SqliteDb
from Util import htmlx
from Util.Log import Log
from Util.ThreadQueue import ThreadQueue
from abc import ABCMeta, abstractmethod
from threading import Thread, Lock
import random
import re
import socket
import time
from collections import deque

class BaseBot(object):
    '''
        The abstract class BaseBot manages the base working of the bot as well as the interface.
        @version: 2.0
    '''
    
    __metaclass__ = ABCMeta
        
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
        Log.write(self.params)
        
        self._regexes = {
                            'name'  :   re.compile(r'^:([^!]+)!([^@]+)@(.*)$'),
                            'url'   :   re.compile(r'\b((?:telnet|ftp|rtsp|https?)://[^/]+[-\w_/?=%&+;#\\@]*)')                         
                         }
        
        self._sock = socket.socket();
        self._success_callback = callback     
        self._lock = Lock()                     # mutex _lock [unused]                
        self.orig_nick = self.params['nick']    # Store original nick for temp logins
        
        BaseBot.reset_flags(self)
        
    def reset_flags(self):
        '''
            @summary: Resets the state flags of the bot 
        '''
        self._retry_timeout = 15                # 15 seconds connection retry                       
        self._voice = True                      # Voice ON or OFF
        self._hearing = True
        self._has_quit = False                  # If a QUIT request was sent by the master
        self._flags = {                         # Flags set on the bot
                            'o' : False,
                            'i' : False,
                            'v' : False
                       }
        
    def close(self):
        '''
            @summary: Request for the termination of bot. This cleanly exits all the threads
        '''
        self._has_quit = True
      
    def close_requested(self):
        '''
            @summary: Whether a valid quit requested was placed or not
        '''
        return self._has_quit
                           
    def cleanup(self):
        '''
            @summary: Performs any cleanup activity while qutting the bot
        '''
        self._sock.close()
            
    def connect(self):
        '''
            @summary: Tries to connect to the IRC Server. Retries after exponential time.
        '''                                
        try:
            self._sock.connect((self.params['host'], self.params['port']))            
            self._retry_timeout = 15
            return True
        except socket.error, e:
            Log.write('Failed to connect %s Reconnecting in %d seconds' % (e, self._retry_timeout))
            time.sleep(self._retry_timeout)
            self._retry_timeout *= 1.5                      # Increase retry time after every failure
    
    def register(self):
        '''
            @summary: Registers the bot on IRC
        '''
        self.send("NICK %s" % self.params['nick'])
        self.send("USER %s %s bla :%s" % (self.params['ident'], self.params['host'], self.params['realname']))
    
    def send(self, msg):
        '''
            @var msg: Message to send
            @summary: Send raw message to IRC
        '''
        try:            
            Log.write('Sending ' + msg)
            self._sock.send(msg + "\r\n")
        except Exception:
            Log.error('QircBot.send: ')        
            
    def begin_read(self):
        '''
            @summary: Launches an async thread for reading
        '''
        self._read_thread = Thread(target=self.read, name='read_thread')
        self._read_thread.start()
        
    def read(self):
        '''
            @summary: Synchronous reading via polling 
        '''        
        try:
            self._read_buffer = ''
            run_read = True
            chunk = '+'                             # Initially chunk not empty
            while run_read:
                self.last_read = time.time()        # Last read time
                chunk = self._sock.recv(2048)               
                if chunk == '':
                    raise Exception('Nothing received. Connection broken.')
                else:                                    # If received something
                    self._read_buffer += chunk                
                    temp = self._read_buffer.split("\n")
                    self._read_buffer = temp.pop()            
                    run_read = self.parse_recv(temp)     # Dispatch message for parsing
                    
        except Exception:
            Log.error('QircBot.read: ') 
                
        self.cleanup()                              # Perform clean up
        self.on_terminate()                
                                                                  
    def done_read(self, seconds):        
        '''
            @summary: Checks if x seconds have elapsed since the last read
        '''
        return (time.time() - self.last_read) < seconds
          
    def start(self):
        '''
            @summary: Starts the bot, does not return until bot is registered
        '''
        Log.write("Starting...")
        while not self.connect():
            try:
                time.sleep(self._retry_timeout)
            except:                 
                pass
        self.register()
        self.begin_read()
        
    
    def on_terminate(self):
        '''
            @summary: Allows for persistence. Reconnects the bot if disconnected by any non-desirable reason
        '''
        pass
    
    @abstractmethod
    def parse_recv(self, recv):
        '''
            @var recv: Message from IRC
            @summary: Parses the messages coming from the IRC to take suitable actions
        '''
        pass        

          
class ActiveBot(BaseBot):
    '''
        ActiveBot allows the bot to perform simple commands and operations.
        @version: 2.0
    '''
       
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
        #BaseBot.__init__(self, callback, params)
        super(ActiveBot, self).__init__(callback, params)
        ActiveBot.reset_flags(self, False)                 # Initialize flags but do not bubble up, since already set by BaseBot.__init__()
        self._op_actions = ThreadQueue()        # ThreadQueue for OP functions
    
    def reset_flags(self, bubble=True):
        '''
            @var bubble: Whether to reset the flags in the base class
            @summary: Resets the state flags of the bot 
        '''
        self._joined = False
        self._pong_recv = True
        self._ghost = False
        if bubble:
            BaseBot.reset_flags(self)
        
    def cleanup(self):
        '''
            @summary: Performs any cleanup activity while qutting the bot
        '''        
        BaseBot.cleanup(self)
        
    def server_ping(self):        
        '''
            @summary: Pings the server every 120 seconds to keep the connection alive
        '''
        counter = 0        
        time.sleep(25)                                                  # Wait 25 seconds for stabilizing                
        while self._pong_recv and not self.close_requested():           # If PONG was received for the previous PING, if not the connection is probably dead            
            self._pong_recv = False            
            counter = 6
            try:                        
                self.ping()                                             # Send PING
            except:
                pass
            while counter:  
                time.sleep(3)                                              # 6*20 second PING              
                counter -= 1                            
        self.ping()                                             # Send FINAL PING
        Log.write('Server Failed to respond to PONG', 'E')
            
    def queue_op_add(self, target, args=(), kwargs={}):
        '''
            @var target: The function
            @var args: Arguments to function
            @var kwargs: Keyworded arguments to function
            @attention: Function name at [0] and arguments after that
            @summary: Adds a item to the queue for processing once the bot is OPed
        '''
        self._lock.acquire()
        self._op_actions.put(target, args, kwargs)
        self._lock.release()
    
    def queue_op_process(self):
        '''
            @summary: Processes the tasks once the bot is OPed
        '''
        self._lock.acquire()        
        self._op_actions.process()          # Process
        self._op_actions.join()             # Block until complete
        self.deop(self.params['chan'], self.params['nick'])
        self._flags['o'] = False                            # Precautionary measure
        self._lock.release()
            
    # Shortcut Functions
    
    def ping(self):
        '''
            @summary: Sends a PING message to the server 
        '''
        self.send("PING %s" % self.params['host'])
        
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
        Log.write("Ghosting nick...")
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
    
    def notice(self, nick, msg):
        '''
            @var nick: User nick or channel
            @var msg: Message to say
            @summary: Whisper something to a channel or user
        '''   
        self.send('NOTICE %s :%s' % (nick, msg))
        
    def kick(self, nick, msg, auto_op=True):        
        '''
            @var nick: User nick
            @var msg: KICK reason
            @var auto_op: If set to true ensures that the bot is +o'd first
            @summary: Kicks a user from the channel
            @attention: Requires OP mode
        '''
        if self._flags['o']:
            self.send('KICK %s %s %s' % (self.params['chan'], nick, ' :'+msg if msg else ''))
        elif auto_op:
            self.queue_op_add(target=self.kick, args=(nick, msg, False,))
            self.op(self.params['chan'], self.params['nick'])
    
    def ban(self, host, reason, auto_op=True):
        '''
            @var host: User's hostmask
            @var reason: KICK reason
            @var auto_op: If set to true ensures that the bot is +o'd first
            @summary: Bans a user from the channel
            @attention: Requires OP mode
        '''
        if self._flags['o']:
            self.send('MODE %s +b %s %s' % (self.params['chan'], host, reason))
        elif auto_op:
            self.queue_op_add(target=self.ban, args=(host, reason, False,))    
            self.op(self.params['chan'], self.params['nick'])
        
    
    def unban(self, host, auto_op=True):    
        '''
            @var host: User's hostmask
            @var auto_op: If set to true ensures that the bot is +o'd first
            @summary: Unbans a user from the channel
            @attention: Requires OP mode
        ''' 
        if self._flags['o']:
            self.send('MODE %s -b %s' % (self.params['chan'], host))
        elif auto_op:
            self.queue_op_add(target=self.unban, args=(host, False,))    
            self.op(self.params['chan'], self.params['nick'])
    
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
    
    def op(self, chan, nick):
        '''
            @var nick: Nick of the user to op
            @var chan: The channel to op to
            @summary: OPs the user in a given channel
        '''
        self.send("PRIVMSG ChanServ :op %s %s" % (chan, nick))
        
    def deop(self, chan, nick):
        '''
            @var nick: Nick of the user to deop
            @var chan: The channel to deop from
            @summary: DEOPs the user in a given channel
        '''
        self.send("PRIVMSG ChanServ :deop %s %s" % (chan, nick))                    
    
    def parse_recv(self, recv):
        '''
            @var recv: Message from IRC
            @summary: Parses the messages coming from the IRC to take suitable actions
        '''
        for line in recv:
            line=str.rstrip(line)        # Strip '\r' characters if present
            line=str.split(line)         # Split elements
            Log.write(' '.join(line))    # Print line
                
            # Important Messages
            if(line[0] == "PING"):                          # PING from server
                return self.recv_ping(line) 
            elif(line[1] == "PONG"):                        # PONG from server
                return self.recv_pong(line)
            elif(line[1] == "QUIT"):                        # QUIT
                return self.recv_quit(line)
            elif(line[1] == "PART"):                        # PART
                return self.recv_part(line)
            elif(line[1] == "JOIN"):                        # JOIN
                return self.recv_join(line)
            elif(line[1] == "KICK"):                        # KICK
                return self.recv_kick(line)
            elif(line[1] == "NOTICE"):                      # NOTICE
                return self.recv_notice(line)
            elif(line[1] == "NICK"):                        # NICK
                return self.recv_nick(line)     
            elif(line[1] == "MODE"):
                return self.recv_mode(line) 
                
            # Control Messages
            elif line[1] == "433":                          # NICK already in use                
                return self.recv_stat_nickuse(line)
            elif line[1] == "376":                          # End of /MOTD command
                return self.recv_stat_endmotd(line)
            elif line[1] == "353":                          # NAMES
                return self.recv_stat_names(line)
            elif line[1] == "366":                          # End of /NAMES list
                return self.recv_stat_endnames(line)              
            elif line[1] == "302":                          # USERHOST
                return self.recv_stat_userhost(line)
                        
            # Basic Messages
            elif line[1] == "PRIVMSG":                
                self.recv_privmsg(line)
                                                           
        return True
    
    def recv_ping(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: Ping was received            
        '''
        self.send("PONG %s" % line[1])   
        return True     
    
    def recv_pong(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: Pong was received            
        ''' 
        self._pong_recv = True
        return True
    
    def recv_quit(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: QUIT was received            
        '''
        m = self._regexes['name'].match(line[0])          # Disconnect read loop
        user = m.group(1)
        if user == self.params['nick']:                    
            if ' '.join(line[2:]) == ":Disconnected by services":   # If bot is disconnected by services then do not retry [GHOSTING]
                self.close()                                                      
            return False                                  # Terminate read thread
        else:
            return True
        
    def recv_part(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: PAR was received            
        '''
        return True
    
    def recv_join(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: JOIN was received            
        '''    
        return True
    
    def recv_kick(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: KICK was received            
        '''
        if line[3] == self.params['nick']:              # If bot is kicked
            self.join(self.params['chan'])  
        return True
    
    def recv_notice(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: NOTICE was received            
        '''
        if ' '.join(line[3:]).find(' has been ghosted') != -1:  # Duplicate NICK has been ghosted
            self.nick(self.orig_nick)                           # Claim original NICK
            self.identify()                                     # Identify
        return True
    
    def recv_nick(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: NICK was received            
        '''
        m = self._regexes['name'].search(line[0]);              # Update nick when changed
        if m.group(1) == self.params['nick']:
            self.params['nick'] = ' '.join(line[2:]).strip(':@+')
            self.on_nick_change()
        return True     
    
    def recv_mode(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: MODE was received            
        '''        
        if len(line) > 4 and line[4] == self.params['nick']:
            mode = line[3][:1]
            if mode == ":":
                mode = line[3][1:2]           
                flags = line[3][2:]
            else:                  
                flags = line[3][1:]
            for c in flags:
                self._flags[c] = (mode == '+')
            
            if mode == '+':
                self.on_mode_set()
            else:
                self.on_mode_reset()
                    
        return True
    
    # Control Messages
    def recv_stat_nickuse(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: The nick is already in use            
        '''                
        if not self._joined:
            self.params['nick'] += str(random.randrange(1,65535)) 
            Log.write('Retrying with nick %s' % self.params['nick'])
            self._ghost = self.params['password'] is not None   # Ghost other user/bot if password is specified
            Log.write("GHOST %s" % self._ghost)
            self.register()                                     # Retry registering
        return True
    
    def recv_stat_endmotd(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: End of MOTD            
        '''
        if self._ghost:                             # If ghosting requested
            self.ghost(self.orig_nick)                    
            self._ghost = False
        else:
            self.identify()                         # Normal join, just identify
        #self._joined = True
        #self._armastep = 0                          # Init armageddon stage to 0
        #self._has_quit = False                      # Initialize vars for PING loop
        self.reset_flags()
        Thread(target=self._success_callback, args=(self,), name='callback').start()    # Call callback function
        Thread(target=self.server_ping, name='ActiveBot.server_ping').start()     # Start pinger thread
        return True
    
    def recv_stat_names(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: NAMES is received
        '''
        self._usernames = [x.strip(':@+') for x in line[5:]] # Get clean names
        return True
    
    def recv_stat_endnames(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: End of NAMES            
        '''            
        return True        
    
    def recv_stat_userhost(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: USERHOST is received          
        '''        
        return True
    
    # Basic Messages
    def recv_privmsg(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: PRIVMSG is received            
        '''        
        return True 
    
    def on_mode_set(self):
        '''
            @summary: Called when a mode is set on the bot
        '''
        pass
    
    def on_mode_reset(self):
        '''
            @summary: Called when a mode is reset on the bot
        '''
        pass

    def on_nick_change(self):
        '''
            @summary: Called when the nick is changed on bot
        '''
        pass
       
    
class QircBot(ActiveBot):
    '''
        @summary: Incorporates complex functionality into the bot
        @version: 2.0
    '''    
      
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
        #ActiveBot.__init__(self, callback, params)
        super(QircBot, self).__init__(callback, params)
        self._qircoptparse = QircOptionParser()
        self._qircdb = SqliteDb()
        
        self._intelli = PseudoIntelligence()    # AI module, Work in development                      
        self._cb = CleverBot()
        self._vote = VoteMaster()
        self._usermsg = {
                            'tell': Tell(),
                            'seen': Seen(self._qircdb),
                            'remind': Remind(self.say)
                         }                
        self._werewolf = Werewolf(callback=self.say, pm=self.notice)
                        
        self._masters = {
                            'admin' :   {
                                            'auth'    : 0,
                                            'members' : ['unaffiliated/nbaztec'],
                                            'powers'  : None
                                        },
                            'mod'   :   {   
                                            'auth'    : 1,                      
                                            'members' : ['unaffiliated/hsr', 'unaffiliated/lfc-fan/x-9923423', 'unaffiliated/ico666'],
                                            'powers'  : ['help', 'voice', 'op', 'deop', 'kick', 'ban', 'unban', 'armageddon', 'arma', 'armarecover']
                                        },
                            'mgr'   :   {                
                                            'auth'    : 2,         
                                            'members' : ['unaffiliated/vy0m', 'unaffiliated/thatsashok', 'unaffiliated/noobjoe'],
                                            'powers'  : ['help', 'voice', 'op', 'deop', 'kick', 'ban', 'unban']
                                        },
                            'others':   {                
                                            'auth'    : 255,         
                                            'members' : ['.*'],
                                            'powers'  : []
                                        }
                         }
        self._special_users = []                        # Prepare special list of users for optimized timings
        for k, v in self._masters.iteritems():
            if k != 'others':                           # Ensure others is last
                self._special_users.append('(?P<%s>%s)' % (k, '|'.join(v['members'])))
        self._special_users.append('(?P<%s>%s)' % ('others', '|'.join(self._masters['others']['members'])))
               
        self._regexes['userhost'] = re.compile(r'([^=]*)=[+-](.*$)')
        self._regexes['special'] = re.compile(r'^:([^!]+)!~*[^@]+@(%s)$' % '|'.join(self._special_users))         # Regex for matching hostmask of users
        self._regexes['cmd'] = re.compile(r'^([\S]+) ?([\S]+)? ?(.+)?$')
        self._regexes['msg'] = re.compile(r'^!(\w+)\s*(.*)$')
        self._regexes['msg-action'] = re.compile(r'^%s[\s,:]+([\S]+)?(?:\s+([\S]+))?(?:\s+(.*))?' % self.params['nick'])        
        self._arma_whitelist = [
                                    'unaffiliated/nbaztec', 'krow\.me', '85\.17\.214\.157',                 # krow.me
                                    'unaffiliated/hsr', 
                                    '204\.176[.\d]+', '59\.178[.\d]+', 'unaffiliated/ico666',
                                    'unaffiliated/lfc-fan/x-9923423',
                                    'unaffiliated/thatsashok',
                                    'services'
                                ]  
        
        self._last5urls = deque(maxlen=5)        # For URL module
        
        self.reset_flags(False)
     
    # Overriden recv methods
    def reset_flags(self, bubble=True):
        '''
            @var bubble: Whether to reset the flags in the base class
            @summary: Resets the state flags of the bot 
        '''
        self._armastep = 0                          # Init armageddon stage to 0
        if bubble:
            ActiveBot.reset_flags(self)
                       
    def recv_join(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: JOIN was received            
        '''
        m = self._regexes['name'].match(line[0])                # Get name of the joining user
        user = m.group(1)
        if user == self.params['nick']:
            self.say('All systems go!')                    
        else:
            self._usermsg['seen'].join(m.group(1),m.group(2),m.group(3))
            #self.say('Hey ' + user)
        return True
    
    def recv_kick(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: KICK was received            
        '''
        if ActiveBot.recv_kick(self, line):
            self._usermsg['seen'].part(line[3],' '.join(line[4:]).lstrip(':'))
            return True
        else:
            return False
    
    def recv_quit(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: QUIT was received            
        '''
        if ActiveBot.recv_quit(self, line):
            m = self._regexes['name'].match(line[0])
            self._usermsg['seen'].part(m.group(1),' '.join(line[3]).lstrip(':'))
            return True        
        else:
            return False
    
    def recv_part(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: PAR was received            
        '''
        m = self._regexes['name'].match(line[0])
        self._usermsg['seen'].part(m.group(1),'PART')
        return True
       
    # Overriden recv_stat methods 
    
    def recv_stat_endnames(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: End of NAMES
            @notice: Used to implement armageddon            
        '''
        Log.write("Usernames %s" % self._usernames)                                
        if self._armastep == 1:                                        
            Thread(target=self.armageddon, name='armageddon-2').start()        
        return True 
    
    def recv_stat_userhost(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: USERHOST is received
            @notice: Used to implement armageddon
        '''
        if self._armastep == 2:                                        
            for uh in line[3:]:                     # Build userhosts
                m = self._regexes['userhost'].search(uh)
                self.userhosts[m.group(1).strip(':@+')] = m.group(2)
                self.username_count -= 1            # Decrement to mark that all usernames were received
            
            if self.username_count == 0:               
                Thread(target=self.armageddon, name='armageddon-3').start()
                Log.write("Userhosts %s" % self.userhosts)                
        return True
    
    def recv_privmsg(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: End of MOTD   
            @notice: Used to implement commands and actions
        '''
        if line[2] == self.params['nick']:  # If message is a privmsg for bot
            m = self._regexes['special'].search(line[0])      # Extract user's details                                                                
            if m:                                             # Check if user is a master of bot
                usr = None                          
                for k in self._masters.iterkeys():
                    if m.group(k):
                        usr = k
                        break;                    
                if usr and (self._hearing or self._masters[usr]['auth'] == 0):    # If a valid user and hearing is enabled or user is admin
                    Thread(target=self.parse_cmd, args=(usr, m.group(1), m.group(2), str.lstrip(' '.join(line[3:]),':'),), name='parse_cmd').start()                        
        elif self._voice:                              
            m = self._regexes['special'].search(line[0])      # Extract user's details                                                                
            if m:              
                usr = None                          
                for k in self._masters.iterkeys():
                    if m.group(k):
                        usr = k
                        break;
                                   
                if usr:                                       # Call extended parser in separate thread                    
                    Thread(target=self.parse_msg, args=(usr, m.group(1), m.group(2), str.lstrip(' '.join(line[3:]),':'),), name='extended_parse').start()
        return True 
    
    #Overriden events
    
    def on_terminate(self):
        '''
            @summary: Allows for persistence. Reconnects the bot if disconnected by any non-desirable reason
            @note: Used to reconnect bot if it's disconnected 
        '''
        if not self.close_requested():                        # Restart was requested
            Log.write("Resurrecting...")            
            self._sock = socket.socket();
            Thread(target=self.start, name='start').start()
        else:    
            self._usermsg['remind'].dispose()
            Log.write("Boom! Owww. *Dead*")
                    
    def on_mode_set(self):        
        '''
            @summary: Called when a mode is set on the bot.
            @note: Used to trigger commands in queue requiring OP
        '''        
        if self._flags['o']:
            if self._armastep == 3:
                self.queue_op_add(target=self.armageddon)                    
            Thread(target=self.queue_op_process, name='QircBot.queue_op_process').start() 
      
    
    # Implementation of parsers  
    def parse_cmd(self, level, nick, host, cmd):
        '''
            @var nick: Nick of user
            @var host: Hostname of user
            @var cmd: Command from standard input
            @summary: Parses the command from PM to bot
        '''                
        m = self._regexes['cmd'].search(cmd)
        if m:
            if self._masters[level]['powers'] is None or m.group(1) in self._masters[level]['powers']:
                if m.group(1) == 'help':
                    if self._masters[level]['powers'] is None:
                        self.notice(nick, 'Commands are: help, quit, restart, op, deop, hearing [on|off], voice [on|off], logging [on|off], say, join, me, notice, kick, ban, unban, arma, armageddon, armarecover')
                    else:
                        self.notice(nick, 'Commands are: %s' % ', '.join(self._masters[level]['powers']))
                elif m.group(1) == 'quit':                      
                    try:
                        self.close()                                            
                        if m.group(2) is not None:
                            self.disconnect(' '.join(filter(None, m.groups()[1:])))                
                        else:
                            self.disconnect("I'll be back.")                                        
                    except Exception:
                        Log.error('QircBot.parse_cmd: ')
                    finally:        
                        Log.stop()        
                        return False
                elif m.group(1) == 'restart':
                        self.disconnect("Restarting")
                elif m.group(1) == 'hearing':
                    if m.group(2):
                        if m.group(2) == 'on':
                            self._hearing = True
                        elif m.group(2) == 'off':
                            self._hearing = False
                    else:
                        self.notice(nick, 'hearing is %s' % ('on' if self._hearing else 'off'))
                elif m.group(1) == 'voice':
                    if m.group(2):
                        if m.group(2) == 'on':
                            self._voice = True
                        elif m.group(2) == 'off':
                            self._voice = False
                    else:
                        self.notice(nick, 'voice is %s' % ('on' if self._voice else 'off'))
                elif m.group(1) == 'logging':
                    if m.group(2):
                        if m.group(2) == 'on':
                            Log.enabled = True
                        elif m.group(2) == 'off':
                            Log.enabled = False
                    else:
                        self.notice(nick, 'logging is %s' % ('on' if Log.enabled else 'off'))
                elif m.group(1) == 'op':
                    if m.group(3):
                        self.op(m.group(2), m.group(3))
                    else:
                        self.op(m.group(2), self.params['nick'])
                elif m.group(1) == 'deop':
                    if m.group(3):
                        self.deop(m.group(2), m.group(3))
                    else:
                        self.deop(m.group(2), self.params['nick'])
                elif m.group(1) == 'say':
                    self.say(' '.join(filter(None, m.groups()[1:])))
                elif m.group(1) == 'join':
                    self.join(m.group(2))
                elif m.group(1) == 'me':
                    self.action(m.group(2))
                elif m.group(1) == 'msg':                
                    self.msg(m.group(2), m.group(3))
                elif m.group(1) == 'notice':
                    self.notice(m.group(2), m.group(3))
                elif m.group(1) == 'kick':
                    self.kick(m.group(2), m.group(3))
                elif m.group(1) == 'ban':                
                    if m.group(3):
                        self.ban(m.group(2), m.group(3))
                    else:
                        self.ban(m.group(2), m.group(2))                    
                elif m.group(1) == 'unban':
                    self.unban(m.group(2))
                elif m.group(1) == 'armageddon':
                    self.armageddon(build=True)
                elif m.group(1) == 'armarecover':
                    self.arma_recover()
                elif m.group(1) == 'arma':
                    if m.group(2):
                        u = []
                        u.append(m.group(2))                    
                        if m.group(3):
                            u.extend(m.group(3).split())
                        self.arma(u)
                else:
                    self.send(cmd)
            else:
                self.notice(nick, 'You are not authorized to perform this operation. Type /msg %s help to see your list of commands' % self.params['nick'])
        return True
                
    def parse_msg(self, level, nick, host, msg):
        '''
            @var nick: Nick of user
            @var host: Hostname of user
            @var msg: Message for bot
            @summary: Specifies additional rules as the general purpose responses
        '''
        Log.write("Extended Message %s" % msg)    
        self.append_if_url(msg)                     # Check for URL
        
        # Tell Messages
        messages = self._usermsg['tell'].get(nick)
        if messages:
            for sender, msg in messages:
                self.say('%s, %s said "%s"' % (nick, sender, msg))
        
        # Commands
        r = None
        
        # Voting
        if self._vote.is_voting:
            if len(msg) == 1:
                self._vote.register_vote(nick, host, msg)
                return True
        if self._werewolf.is_joining:
            if msg == "+":
                self._werewolf.join(nick)
                return True
        elif self._werewolf.is_playing:
            m = re.search(r'\+ ?([\S]*)', msg)
            if m:
                self._werewolf.lynch(nick, m.group(1))
                return True
               
        use_nick = False
        silence = True

        m = self._regexes['msg'].search(msg)        
        if m:    
            use_nick = True                             # If it's a command then use nick to address the caller
            silence = False
            #if m.group(2):                              # Explode flags
            #    flags = list(m.group(2))
            #else:
            #    flags = []
            options = None            
            
            if m.group(1) == 'help':                
                self.send_multiline(self.notice, nick, """Enter <command> -h for help on the respective command
Commands: 
    !help             Shows this help
    !search, !s       Search for a term on various sites
    !calc, !c         Perform some calculation
    !define, !d       Get the meaning, antonyms, etc, for a term
    !weather, !w      Get weather and forecasts for a location
    !locate, !l       Locate a user, IP or coordinate
    !url              Perform operation on an url, 
                      Use %N (max 5) to access an earlier url
    !user             Perform operation related to user
    !vote             Start a vote
    !roll             Roll a dice
    !game             Begin a game""")
                silence = True
            else:
                (cmd_msg, options, args) = self._qircoptparse.parse(m.group(1), m.group(2).split())                
                if cmd_msg is None:
                    silence = True
                else:
                    if args is None:
                        self.send_multiline(self.notice, nick, options)
                        silence = True
                    else:
                        args = ' '.join(args)
                        # Use default options as the last item of the if-else ladder
                        # If they are first then they'll be used irrespective of other flags,
                        # Since the default options are always True
                        if cmd_msg == 'search':
                            if options.custom:
                                r = Search.customsearch(args, options.custom, options.result, options.single)              
                            elif options.gimage:
                                r = Search.googleimage(args, options.result, options.single)
                            elif options.youtube:
                                r = Search.youtube(args, options.result, options.single)
                            elif options.wiki:
                                r = Search.wiki(args, options.result, options.single)
                            elif options.imdb:
                                r = Search.imdb(args, options.result, options.single)
                            elif options.tdf:
                                r = Search.tdf(args, options.result, options.single)
                            elif options.google:
                                r = Search.google(args, options.result, options.single)
                        elif cmd_msg == 'calc':                                            
                            if options.google:
                                r = Calc.googlecalc(args)
                            elif options.wolf:
                                r = Calc.wolfram(args)
                        elif cmd_msg == 'define':                        
                            if options.google:
                                r = Define.googledefine(args, options.result)
                            elif options.dictionary:
                                pass                                        # TODO: Alternative source of dictionary
                            elif options.antonym:
                                pass                                        # TODO: Antonym
                            elif options.etymology:
                                pass                                        # TODO: Etymology
                            elif options.urban:
                                r = Define.urbandefine(args, options.result)
                        elif cmd_msg == 'weather':
                            if options.forecast:
                                r = Weather.forecast(args, options.days)
                            else:
                                r = Weather.weather(args)
                        elif cmd_msg == 'locate':
                            if options.ip:
                                r = Locate.iplocate(options.ip)
                            elif options.coord:
                                l = options.coord.split(',')
                                r = Locate.geo(l[0], l[1])
                        elif cmd_msg == 'user':
                            if options.tell:
                                self._usermsg['tell'].post(nick, options.tell, args)
                                self.notice(nick, 'Ok, I will convey the message to %s' % options.tell)
                                silence = True
                            elif options.remind:         
                                silence = True
                                try:                   
                                    r = self._usermsg['remind'].remind(nick, options.remind, args)
                                    self.notice(nick, 'Reminder has been set')
                                except Remind.RemindFormatError:
                                    self.notice(nick, 'Invalid time format. Example 20s, 2m, 3h...')
                                except Remind.RemindValueError, e:
                                    self.notice(nick, e.message)
                            elif options.seen:                            
                                r = self._usermsg['seen'].seen(args)                                                                
                        elif cmd_msg == 'url':                            
                            try:
                                m = re.match(r'^%(\d)$', args)                            
                                if m:
                                    args = self._last5urls[int(m.group(1))-1]                                                                       
                            except Exception:
                                r = 'No url exists for %' + m.group(1)
                            else:
                                if args.find('://', 0, 10) == -1:
                                    args = 'http://' + args
                                if options.title:
                                    r = Url.title(args)
                                elif options.content:
                                    r = Url.content_type(args)
                                elif options.preview:
                                    r = Url.description(args)
                                elif options.short:
                                    r = Url.googleshort(args)
                                elif options.expand:
                                    r = Url.googleexpand(args)
                                elif options.port:
                                    r = Url.port(args, options.port)
                                elif options.dns:                            
                                    r = Url.dns(args)
                                if r is None:                                   # Silence if no results
                                    silence = True                                                                                            
                        elif cmd_msg == 'vote':                                                
                            if options.kick:                
                                if self._masters[level]['auth'] < 3:                    
                                    msg_u = args.split(' ')
                                    kick_users = msg_u[0]
                                    kick_reason = ' '.join(msg_u[1:])                    
                                    # Define callback                    
                                    def vote_result(p, n, q):                                        
                                        if (p+n) > 1:
                                            vote = p - n
                                            if vote > 0:                        
                                                self.say('The general public (%d) has agreed to kick %s' % (p + n, kick_users))
                                                for u in kick_users.split(','):
                                                    self.kick(u, kick_reason)
                                            elif vote < 0:                        
                                                self.say('The general public (%d) has disagreed to kick %s' % (p + n, kick_users))
                                            else:
                                                self.say('The outcome is a draw! %s is/are saved.' % kick_users)
                                        else:
                                            self.say('A minimum of 2 votes are required for taking decision.')
                                    # Call
                                    self._vote.start(options.interval, 'kick %s %s' % (kick_users, kick_reason), self.say, vote_result)                
                                silence = True
                            elif options.arma:                                                                        
                                if self._masters[level]['auth'] < 3:                                
                                    # Define calback
                                    def vote_result(p, n, q):
                                        if (p+n) > 1:
                                            vote = p - n
                                            if vote > 0:
                                                self.say('The general public (%d) has agreed to bring forth armageddon upon %s' % (p + n, args))                            
                                                self.arma(args.split())
                                            elif vote < 0:
                                                self.say('The general public (%d) has disagreed to bring forth armageddon upon %s' % (p + n, args))
                                            else:
                                                self.say('The outcome is a draw! %s is/are saved.' % args)
                                        else:
                                            self.say('A minimum of 2 votes are required for taking decision.')
                                    # Call    
                                    self._vote.start(options.interval, 'Bring forth armageddon upon %s?' % args, self.say, vote_result)                
                                silence = True
                            else:                                       # Regular vote
                                def vote_result(p, n, q):
                                    vote = p - n
                                    if vote:
                                        self.say('The general public (%d) %s : %s' % ((p + n), 'agrees' if vote > 0 else 'disagrees', q))
                                    else:
                                        self.say('The outcome is a draw! Bummer.')
                                self._vote.start(options.interval, args, self.say, vote_result)                
                                silence = True
                        elif cmd_msg == 'roll':
                            if options.min > 0 and options.max > 0 and options.min < options.max:
                                r = '%s rolled a %s.' % (nick, Roll.roll(options.min, options.max))
                                use_nick = False
                        elif cmd_msg == 'game':
                            if args == 'werewolf':
                                #r = self._werewolf.start()
                                r = 'Game is currently offline'
                                use_nick = False
                            else:
                                r = "-werewolf"
                                use_nick = False                    
                        else:
                            silence = True        
        else:
            use_nick = False    
            m = self._regexes['msg-action'].search(msg)            
            if m:
                #if m.group(1) == 'tell':
                #    self._usermsg['tell'].post(nick, m.group(2), m.group(3))
                #    self.notice(nick, 'Ok, I will convey the message to %s' % m.group(2))                
                if self.parse_verb(m.group(1), m.group(2), m.group(3)):   # Call a function for additional operation, which can be extended later
                    pass
                else:
                    clean_msg = filter(None, m.groups())
                    reply = self._intelli.reply(msg, nick)                  # Use AI for replying
                    if not reply:  
                        reply = self._cb.ask(clean_msg)
                    if reply:                                               # If there's some valid reply                  
                        reply = htmlx.unescape(reply)
                        self.say(reply)                                         # Use AI for replying   
        # Say if some output was returned
        if r:
            r = r[:255]
            if use_nick:   
                r = nick + ', ' + r
                             
            if options and options.private:
                self.notice(nick, r)
            else:
                self.say(r)
        elif not silence:
            if options and options.private:
                self.notice(nick, "No results for you")
            else:
                self.say("No results for you %s." % nick)                              
            
    def parse_verb(self, verb, nick, text):
        '''
            @var verb: The action text
            @var nick: The nick part
            @var text: The text message
            @summary: Parses verbs to present action for the bot 
        '''                
        if verb in ['dodge', 'give', 'steal', 'take', 'catch', 'arm', 'engage', 'assault', 'launch', 'slit', 'poke', 'strip', 'disarm', 'fire', 'attack', 'chase', 'create', 'make', 'relieve', 'show', 'escort', 'push', 'pull', 'throw', 'feed', 'fuck', 'sell', 'buy', 'oblige', 'demolish', 'destroy']:
            verb += 'es' if verb.endswith(('s', 'z', 'x', 'sh', 'ch'), -2) else 's'            
            if nick is not None:
                if text is None:
                    text = ''
                self.action('%s %s %s' % (verb, nick, text))
        elif verb == 'slap':
            self.action('bitchslaps %s' % (nick))
        else:
            return False
        return True
        
    # WARNING: Do you know what you are doing?
    def armageddon(self, build=False):  
        '''
            @var build: True if called for first time, from stage 0. False otherwise.
            @summary: Does what it says. Armageddon.
                      Kickbans all users except the ones in whitelist
        '''              
        if build and self._armastep == 0:               # Stage 1, Prepare usernames
            self._armastep += 1
            self._usernames = []
            self.names()
        elif self._armastep == 1:                       # Stage 2, Prepare userhosts
            self._armastep += 1         
            self.userhosts = {}                         # Fresh list of userhosts
            try:
                self._usernames.remove(self.params['nick']) # Remove bot's nick from the list
            except:
                pass
            self.username_count = len(self._usernames)
            for uchunk in self.chunk(self._usernames, 5):   
                self.send("USERHOST %s" % ' '.join(uchunk))
        elif self._armastep == 2:                       # Stage 3, Get +o mode {optional}
            self._armastep += 1            
            #self.send("PRIVMSG ChanServ :op %s %s" % (self.params['chan'], self.params['nick']))
            self.op(self.params['chan'], self.params['nick'])
            #Thread(target=self.armageddon, name='armageddon-4').start()  
        else:                                           # Final Stage, kickban everyone except in whitelist
            self._armastep = 0                          # Reset armageddon to Stage 0
            self._arma_resetlist = []
            regx = re.compile(r'^[^@]*@(%s)' % '|'.join(self._arma_whitelist)) 
            for u,h in self.userhosts.iteritems():                                         
                if  regx.match(h) is None:                                        
                    Log.write('armageddon-kickban %s %s' % (u, h))
                    self.ban('*!' + h, 'ARMAGEDDON', False)
                    self._arma_resetlist.append('*!' + h)
                    self.kick(u, 'ARMAGEDDON', False)    
                else:
                    Log.write('Saved %s %s' % (u, h))
    
    def arma(self, usernames):
        '''
            @var usernames: The list of users to bring forth armageddon upon
            @summary: A toned down version of armageddon kickbanning only selected users 
        '''
        self._armastep = 1        
        self._usernames = usernames 
        self.armageddon()    
    
    def arma_recover(self, auto_op=True):
        '''
            @var auto_op: If set to true ensures that the bot is +o'd first
            @summary: Recovers from the armageddon by unbanning all the people previously banned
        '''
        if self._flags['o']:
            for u in self._arma_resetlist:
                self.unban(u, False)
        elif auto_op:
            self.queue_op_add(target=self.arma_recover, args=(False,)) 
            self.op(self.params['chan'], self.params['nick'])  
            
    def send_multiline(self, method, nick, lines):                
        for line in lines.split('\n'):
            method(nick, line)        
    
    def append_if_url(self, msg):        
        '''
            @var msg: 
        '''
        m = self._regexes['url'].search(msg)
        if m is not None:
            if len(self._last5urls) == 5:
                self._last5urls.pop()
            self._last5urls.appendleft(m.group(0))            
        
    def chunk(self,l, n):
        '''
            @var l: The list to chunk
            @var n: Number of elements per chunk
            @summary: Splits a list into chunks having n elements each
        '''
        return [l[i:i+n] for i in range(0, len(l), n)]