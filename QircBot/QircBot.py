'''
Created on Jun 7, 2012
@author: Nisheeth
@version: 3.0 Deadpool
'''

from Modules.Manager import ModuleManager, CommandManager
from Modules.Commands import JoinModule, QuitModule, KickModule, BanModule, OpModule, SayModule, ArmageddonModule, FlagModule, EnforceModule, UserAuthModule, ModManagerModule
from Modules.Internal import SearchModule, CalculationModule, DefinitionModule, QuoteModule, WeatherModule, LocationModule, UrlModule, UserModule, VoteModule, RollModule, GameModule, VerbModule, CleverModule
from Interfaces.BotInterface import VerbalInterface, EnforcerInterface, CompleteInterface
        
from QircDatabase import SqliteDb
from Util.Log import Log
from Util.ThreadQueue import ThreadQueue
from abc import ABCMeta, abstractmethod
from threading import Thread, Lock
from os import path
import random
import re
import socket
import time
import cPickle

class BaseBot(object):
    '''
        The abstract class BaseBot manages the base working of the bot as well as the interface.
        @version: 3.0
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
              'password'    : 'None',
              'chan'        : []           
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
        
    def reset_flags(self, build=True):
        '''
            @var build: If true, then status_flags are initialized 
            @summary: Resets the state flags of the bot 
        '''
        self._retry_timeout = 15                # 15 seconds connection retry                               
        self._has_quit = False                  # If a QUIT request was sent by the master
        if build:       
            self._status_flags = {
                              'hear' : True,
                              'voice'   : True,
                              'log' : True,
                              'kick'    : True,
                              'ban'     : True,
                              'arma'    : True,
                              'talk'    : True,
                              'url'     : False
                          }
     
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
            msg = msg[:510]     # Max limit is 512 (2 for CRLF)
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
        self.on_bot_terminate()                
                  
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
        self.on_connected()
        
    
    def on_bot_terminate(self):
        '''
            @summary: Called when the bot terminates
        '''
        pass
    
    def on_connected(self):
        '''
            @summary: Called when the bot is connected
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
        @version: 3.0
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
        from Modules.Commands import LogModule
        self._logger = LogModule()
        self._logger.enabled(True)
    
    @property
    def current_channel(self):
        '''
            @summary: Returns the current channel or an empty string 
        '''
        if len(self.params['chan']):
            return self.params['chan'][0]
        else:
            return ''
        
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
        while self._pong_recv and not self.close_requested():           # If PONG was received for the previous PING, if not the connection is probably dead            
            self._pong_recv = False            
            counter = 6
            try:                        
                time.sleep(45)                                          # PING every 45 seconds
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
        if self._op_actions.Length:        
            self._op_actions.process()          # Process
            self._op_actions.join()             # Block until complete
            self.deop(self.current_channel, self.params['nick'])
            self._flags['o'] = False                            # Precautionary measure
        self._lock.release()
            
    # Shortcut Functions
    
    def ping(self):
        '''
            @summary: Sends a PING message to the server 
        '''
        self.send("PING %s" % self.params['host'])
        
    def join(self, chan, key=''):
        '''
            @var chan: The channel to join. Example #chan
            @summary: Sends a JOIN command to join the channel and updates the current channel
        '''                
        self.send("JOIN "+chan+" "+key)
        
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
        self.send('PRIVMSG %s :%s' % (self.current_channel, msg))
        
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
        
    def send_multiline(self, method, nick, lines):
        '''
            @var method: The method to use to send the message
            @var nick: The user to send the message to, if applicable
            @var lines: A multiline message string
        '''             
        for line in lines.split('\n'):
            if nick:
                method(nick, line)
            else:
                method(line)        
            
    def kick(self, nick, msg, auto_op=True):        
        '''
            @var nick: User nick
            @var msg: KICK reason
            @var auto_op: If set to true ensures that the bot is +o'd first
            @summary: Kicks a user from the channel
            @attention: Requires OP mode
        '''
        if self._flags['o']:
            self.send('KICK %s %s %s' % (self.current_channel, nick, ' :'+msg if msg else ''))
        elif auto_op:
            self.queue_op_add(target=self.kick, args=(nick, msg, False,))
            self.op(self.current_channel, self.params['nick'])
    
    def ban(self, host, auto_op=True):
        '''
            @var host: User's hostmask
            @var auto_op: If set to true ensures that the bot is +o'd first
            @summary: Bans a user from the channel
            @attention: Requires OP mode
        '''
        if self._flags['o']:
            self.send('MODE %s +b %s' % (self.current_channel, host,))
        elif auto_op:
            self.queue_op_add(target=self.ban, args=(host, False,))    
            self.op(self.current_channel, self.params['nick'])
        
    
    def unban(self, host, auto_op=True):    
        '''
            @var host: User's hostmask
            @var auto_op: If set to true ensures that the bot is +o'd first
            @summary: Unbans a user from the channel
            @attention: Requires OP mode
        ''' 
        if self._flags['o']:
            self.send('MODE %s -b %s' % (self.current_channel, host))
        elif auto_op:
            self.queue_op_add(target=self.unban, args=(host, False,))    
            self.op(self.current_channel, self.params['nick'])
    
    def names(self): 
        '''
            @summary: Send a NAME command to get the list of usernames in the current channel
        '''       
        self.send('NAMES %s' % self.current_channel)        
    
    def action(self, msg):
        '''
            @var msg: Message to display
            @summary: Send an ACTION message
        '''
        self.send("PRIVMSG %s :\x01ACTION %s\x01" % (self.current_channel, msg))
    
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
            @var recv: Messages from IRC
            @summary: Parses the messages coming from the IRC to take suitable actions
        '''
        for line in recv:
            line=str.rstrip(line)        # Strip '\r' characters if present
            line=str.split(line)         # Split elements
            Log.write(' '.join(line))    # Print line
                
            # Important Messages
            if(line[0] == "PING"):                          # PING from server
                return self.cmd_ping(line) 
            elif(line[1] == "PONG"):                        # PONG from server
                return self.cmd_pong(line)
            elif(line[1] == "QUIT"):                        # QUIT
                return self.cmd_quit(line)
            elif(line[1] == "PART"):                        # PART
                return self.cmd_part(line)
            elif(line[1] == "JOIN"):                        # JOIN
                return self.cmd_join(line)
            elif(line[1] == "KICK"):                        # KICK
                return self.cmd_kick(line)
            elif(line[1] == "NOTICE"):                      # NOTICE
                return self.cmd_notice(line)
            elif(line[1] == "NICK"):                        # NICK
                return self.cmd_nick(line)     
            elif(line[1] == "MODE"):
                return self.cmd_mode(line) 
                
            # Control Messages
            elif line[1] == "433":                          # NICK already in use                
                return self.stat_nickuse(line)
            elif line[1] == "375":                          # Start of /MOTD command
                return self.stat_startmotd(line)
            elif line[1] == "371" or line[1] == "372":      # MOTD                
                self.stat_motd(line)
            elif line[1] == "376":                          # End of /MOTD command
                return self.stat_endmotd(line)
            elif line[1] == "353":                          # NAMES
                self.stat_names(line)
            elif line[1] == "366":                          # End of /NAMES list
                return self.stat_endnames(line)              
            elif line[1] == "302":                          # USERHOST
                self.stat_userhost(line)            
            elif line[1] == "462":                          # Already registered
                return self.stat_already_registered(line)   
            # Basic Messages
            elif line[1] == "PRIVMSG":                
                self.cmd_privmsg(line)
                                                           
        return True
    
    def cmd_ping(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: Ping was received            
        '''
        self.send("PONG %s" % line[1])
        return self.recv_ping(line[1]) 
    
    def cmd_pong(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: Pong was received            
        ''' 
        self._pong_recv = True
        return self.recv_pong(line[0], line[-1])
    
    def cmd_quit(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: QUIT was received            
        '''
        return self.recv_quit(line[0], ' '.join(line[2:]).lstrip(':'))
        
        
    def cmd_part(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: PAR was received            
        '''
        return self.recv_part(line[0], line[2], ' '.join(line[3:]).lstrip(':'))
    
    def cmd_join(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: JOIN was received            
        '''    
        return self.recv_join(line[0], line[2])
    
    def cmd_kick(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: KICK was received            
        '''
        return self.recv_kick(line[0], line[2], line[3], ' '.join(line[4:]).lstrip(':'))
    
    def cmd_notice(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: NOTICE was received            
        '''
        return self.recv_notice(line[0], ' '.join(line[3:]))        
    
    def cmd_nick(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: NICK was received            
        '''
        return self.recv_nick(line[0], line[2])
    
    def cmd_mode(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: MODE was received            
        ''' 
        return self.recv_mode(line[0], line[2], line[3], line[4:])       
    
    def cmd_privmsg(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: PRIVMSG is received            
        '''        
        return self.recv_privmsg(line[0], line[2], ' '.join(line[3:])) 
           
    # Control Messages
    def stat_nickuse(self, line):
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
    
    def stat_startmotd(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: Start of MOTD            
        '''
        return True
    
    def stat_motd(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: Content of MOTD            
        '''
        return True
    
    def stat_endmotd(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: End of MOTD            
        '''
        if self._ghost:                             # If ghosting requested
            self.ghost(self.orig_nick)                    
            self._ghost = False
        else:
            self.identify()                         # Normal join, just identify
        
        self.reset_flags(build=False)               # Give bot a fresh start
        Thread(target=self._success_callback, args=(self,), name='callback').start()    # Call callback function
        Thread(target=self.server_ping, name='ActiveBot.server_ping').start()     # Start pinger thread
        return True
    
    def stat_names(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: NAMES is received
        '''
        self._usernames = [x.strip(':@+') for x in line[5:]] # Get clean names
        return True
    
    def stat_endnames(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: End of NAMES            
        '''            
        return True        
    
    def stat_userhost(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: USERHOST is received          
        '''        
        return True
        
    def stat_already_registered(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: ERR_ALREADYREGISTERED is received          
        '''        
        return self.stat_endmotd(line)
    
    def recv_ping(self, server):
        '''
            @var server: The server that sent PING
        '''
        return True
    
    def recv_pong(self, server, msg):
        '''
            @var server: The server that sent the PONG
            @var channel: PONG message
        '''
        return True  
        
    def recv_quit(self, user, reason):
        '''
            @var user: The user that parted
            @var reason: The reason for quit
        '''
        self._logger.quit(user, reason)
        m = self._regexes['name'].match(user)          # Disconnect read loop
        user = m.group(1)
        if user == self.params['nick']:                    
            if reason == "Disconnected by services":   # If bot is disconnected by services then do not retry [GHOSTING]
                self.close()                                                      
            return False                                  # Terminate read thread
        else:
            return True
    
    def recv_part(self, user, channel, reason):
        '''
            @var user: The user that parted
            @var channel: The channel that was parted from
        '''
        m = self._regexes['name'].match(user)    
        if m.group(1) == self.params['nick']:
            self.on_bot_part(channel)
        self._logger.parted(user, channel, reason)
        return True
    
    def recv_join(self, user, channel ):
        '''
            @var user: The user that joined
            @var channel: The channel that was joined to
        '''
        self._logger.joined(user, channel)
        m = self._regexes['name'].match(user)            
        if m.group(1) == self.params['nick']:
            self.on_bot_join(channel)        
        return True
    
    def recv_kick(self, source, channel, user, reason):
        '''
            @var source: The user who issued the KICK
            @var channel: The channel on which KICK was issued
            @var user: The user who got kicked
            @var reason: The reason for kicking 
        '''
        self._logger.kicked(source, user, channel, reason)
        if user == self.params['nick']:                         # If bot is kicked
            self.join(channel)  
        return True
    
    def recv_notice(self, source, msg):
        '''
            @var source: The source of the NOTICE
            @var source: The message received
        '''
        if msg.find(' has been ghosted') != -1:                 # Duplicate NICK has been ghosted
            self.nick(self.orig_nick)                           # Claim original NICK
            self.identify()                                     # Identify
        return True
    
    def recv_nick(self, user, new_nick):
        '''
            @var user: The user who issued NICK
            @var new_nick: The new NICK
        '''
        self._logger.nick(user, new_nick)
        m = self._regexes['name'].search(user);              # Update nick when changed
        if m.group(1) == self.params['nick']:
            self.params['nick'] = new_nick.strip(':@+')
            self.on_bot_nick_change(self.params['nick'])
        return True
    
    def recv_mode(self, source, channel, flags, users):
        '''
            @var source: The user who issued the KICK
            @var channel: The channel on which KICK was issued
            @var mode: Flags set or reset (+ or -)
            @var flags: The flags issued
            @var users: The users specified
        '''        
        self._logger.mode(source, channel, flags, ', '.join(users))
        if self.params['nick'] in users:    # Mode is set on an user and not on channel (hence the 4th index)
            mode = flags[0]
            if mode == ":":
                mode = flags[1:2]           
                flags = flags[2:]
            else:                  
                flags = flags[1:]            
        
            for c in flags:
                self._flags[c] = (mode == '+')
                
            if mode == '+':
                self.on_bot_mode_set()
            else:
                self.on_bot_mode_reset()
        return True
    
    def recv_privmsg(self, user, channel, msg):
        '''
            @var source: The user sending the PRIVMSG
            @var source: The message received
        '''
        if channel == self.current_channel:
            self._logger.msg(user, None, msg.lstrip(':'))
        else:
            self._logger.msg(user, channel, msg.lstrip(':'))
        return True
    
    def on_bot_join(self, channel):
        '''
            @var channel: The channel name
            @summary: Called when the bot joins a channel
        '''          
        if channel not in self.params['chan']: 
            self.params['chan'].insert(0, channel)     # Reset  channel from state, if parted
    
    def on_bot_part(self, channel):
        '''
            @var channel: The channel name
            @summary: Called when the bot parts the channel
        '''        
        if channel in self.params['chan']: 
            self.params['chan'].remove(channel)     # Reset  channel from state, if parted
    
    def on_bot_mode_set(self):
        '''
            @summary: Called when a mode is set on the bot
        '''
        pass
    
    def on_bot_mode_reset(self):
        '''
            @summary: Called when a mode is reset on the bot
        '''
        pass

    def on_bot_nick_change(self, nick):
        '''
            @var nick: The new nick
            @summary: Called when the nick is changed on bot
        '''
        pass
    
class ArmageddonBot(ActiveBot):
    '''
        @summary: Incorporates complex functionality into the bot
        @version: 3.0
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
        super(QircBot, self).__init__(callback, params)
        self.reset_flags(False)
                
        self._masters = {
                            'admin' :   {
                                            'auth'    : 0,
                                            'members' : ['unaffiliated/nbaztec'],
                                            'powers'  : None
                                        },
                            'mod'   :   {   
                                            'auth'    : 1,                      
                                            'members' : [],
                                            'powers'  : ['help', 'flags', 'op', 'kick', 'enforce', 'ban', 'module', 'users', 'armageddon']
                                        },
                            'mgr'   :   {                
                                            'auth'    : 2,         
                                            'members' : [],
                                            'powers'  : ['help', 'flags', 'op', 'kick', 'enforce', 'ban', 'unban']
                                        },
                            'others':   {                
                                            'auth'    : 255,         
                                            'members' : ['.*'],
                                            'powers'  : ['help']
                                        }
                         }
                
        self._arma_whitelist = None
        self._arma_resetlist = None
        self._qircdb = SqliteDb()
        
        # Interfaces
        verbal_interface = VerbalInterface(self)
        enforcer_interface = EnforcerInterface(self)
        complete_interface = CompleteInterface(self)
        
        # Module Managers
        self._modmgr = ModuleManager()   
        self._cmdmgr = CommandManager()
        
        # Load state
        self.load_state()
        
        # Add Modules
        self._modmgr.add('search', SearchModule(verbal_interface), ['s', 'g'])
        self._modmgr.add('calc', CalculationModule(verbal_interface), ['c'])
        self._modmgr.add('define', DefinitionModule(verbal_interface), ['d'])
        self._modmgr.add('quote', QuoteModule(verbal_interface))
        self._modmgr.add('weather', WeatherModule(verbal_interface), ['w'])
        self._modmgr.add('locate', LocationModule(verbal_interface), ['l'])
        self._modmgr.add('url', UrlModule(verbal_interface))
        self._modmgr.add('user', UserModule(enforcer_interface, self._qircdb))
        self._modmgr.add('vote', VoteModule(enforcer_interface))
        self._modmgr.add('roll', RollModule(verbal_interface))
        self._modmgr.add('game', GameModule(verbal_interface))            
        self._modmgr.add_intelligence(VerbModule(verbal_interface))
        self._modmgr.add_intelligence(CleverModule(verbal_interface, self.params['nick']))
        self._modmgr.disable_module('game')
     
        self._cmdmgr.add('join', JoinModule(complete_interface))
        self._cmdmgr.add('quit', QuitModule(complete_interface))
        self._cmdmgr.add('kick', KickModule(complete_interface))
        self._cmdmgr.add('ban', BanModule(complete_interface))
        self._cmdmgr.add('op', OpModule(complete_interface))
        self._cmdmgr.add('say', SayModule(complete_interface))
        self._cmdmgr.add('armageddon', ArmageddonModule(complete_interface, [
                                    'unaffiliated/nbaztec', 'krow\.me', '85\.17\.214\.157',                 # krow.me
                                    'unaffiliated/hsr', 
                                    '204\.176[.\d]+', '59\.178[.\d]+', 'unaffiliated/ico666',
                                    'unaffiliated/lfc-fan/x-9923423',
                                    'unaffiliated/thatsashok',
                                    'services'
                                ]))
        self._cmdmgr.add('flags', FlagModule(complete_interface))
        self._cmdmgr.add('enforce', EnforceModule(complete_interface))
        self._cmdmgr.add('users', UserAuthModule(complete_interface))
        self._cmdmgr.add('module', ModManagerModule(complete_interface))
        
        # Prepare Regexes                       
        self._regexes['userhost'] = re.compile(r'([^=]*)=[+-](.*$)')        
        self._regexes['cmd'] = re.compile(r'^([\S]+) ?(.*)$')
        self._regexes['module-cmd'] = re.compile(r'^!(\w+)\s*(.*)$')
        self._regexes['module-reply'] = re.compile(r'^%s[\s,:]+(.+)$' % self.params['nick'])
        self.regex_prepare_users()
        
    def regex_prepare_users(self):
        '''
            @summary: Prepare a list of master and compiles the regex
        '''
        self._special_users = []                        # Prepare special list of users for optimizing match timings
        for k, v in self._masters.iteritems():
            if k != 'others':                           # Ensure others is last
                self._special_users.append('(?P<%s>%s)' % (k, '|'.join(v['members'])))
        self._special_users.append('(?P<%s>%s)' % ('others', '|'.join(self._masters['others']['members'])))
        self._regexes['special'] = re.compile(r'^:([^!]+)!~*[^@]+@(%s)$' % '|'.join(self._special_users))         # Regex for matching hostmask of users
        
    def get_status_flag(self, key=None):
        '''
            @var key: Key to status
            @return: Returns True if the status is set, else False
        '''
        if key is None:
            return self._status_flags.items()
        else:            
            return self._status_flags[key]
            
    def status_flag(self, key=None, value=None, flag_dict=False):
        '''
            @var key: Key to status
            @var value: The new value to set, if required 
            @var flag_dict: If true, then the original dict is set/returned
            @return: Returns True if the status is set, else False
        '''
        if flag_dict:
            if value is None:
                return self._status_flags
            else:        
                self._status_flags = value
        else:
            if key is None:
                return self._status_flags.items()
            else:
                if value is not None:
                    self._status_flags[key] = value
                    return value
                else:
                    return self._status_flags[key]
            
            
    def get_module(self, key):
        '''
            @var key: Returns a module specified by the key
        '''
        return self._modmgr.module(key)
    
    # Overriden recv methods
    def reset_flags(self, bubble=True, build=True):
        '''
            @var bubble: Whether to reset the flags in the base class
            @summary: Resets the state flags of the bot 
        '''
        self._armastep = 0                          # Init armageddon stage to 0
        if bubble:
            super(ArmageddonBot, self).reset_flags(build)
                       
    def cmd_join(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: JOIN was received            
        '''        
        #user = m.group(1)
        #if user == self.params['nick']:
        #    self.say('All systems go!')
        m = self._regexes['name'].match(line[0])                # Get name of the joining user                    
        if m.group(1) != self.params['nick']:                   # If user is not our bot
            self._cmdmgr.module('enforce').enforce(line[0].lstrip(':@+'))
            self._modmgr.module('user').seen_join(m.group(1),m.group(2),m.group(3))
            #self.say('Hey ' + user)                            # Greet user
        return super(ArmageddonBot, self).cmd_join(line)
    
    def on_bot_join(self, channel):
        '''
            @var channel: The channel name
            @summary: Called when the bot joins a channel
        ''' 
        super(ArmageddonBot, self).on_bot_join(channel)
        self.say('All systems go!')
        
    def cmd_nick(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: NICK was received            
        '''
        if super(ArmageddonBot, self).cmd_nick(line):            
            m = self._regexes['name'].search(line[0])
            self._cmdmgr.module('enforce').enforce('%s!%s@%s' % (' '.join(line[2:]).strip(':@+'), m.group(2), m.group(3)))
            return True
        else:
            return False   
    
    def cmd_kick(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: KICK was received            
        '''
        if super(ArmageddonBot, self).cmd_kick(line):
            self._modmgr.module('user').seen_part(line[3],' '.join(line[4:]).lstrip(':'))
            return True
        else:
            return False
    
    def cmd_quit(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: QUIT was received            
        '''
        if super(ArmageddonBot, self).cmd_quit(line):
            m = self._regexes['name'].match(line[0])
            self._modmgr.module('user').seen_part(m.group(1),' '.join(line[3]).lstrip(':'))
            return True        
        else:
            return False
    
    def cmd_part(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: PAR was received            
        '''
        m = self._regexes['name'].match(line[0])
        self._modmgr.module('user').seen_part(m.group(1),'PART')
        return super(ArmageddonBot, self).cmd_part(line)
       
    # Overriden stat methods 
    
    def stat_endnames(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: End of NAMES
            @notice: Used to implement armageddon            
        '''
        Log.write("Usernames %s" % self._usernames)                                
        if self._armastep == 1:                                        
            Thread(target=self.armageddon, name='armageddon-2').start()        
        return True 
    
    def stat_userhost(self, line):
        '''
            @var line: The text received broken into tokens
            @summary: USERHOST is received
            @notice: Used to implement armageddon
        '''
        if self._armastep == 2:  
            for uh in line[3:]:                     # Build userhosts
                m = self._regexes['userhost'].search(uh)
                if m:
                    self.userhosts[m.group(1).strip(':@+')] = m.group(2)
                    self.username_count -= 1            # Decrement to mark that all usernames were received
            
            if self.username_count == 0:               
                Thread(target=self.armageddon, name='armageddon-3').start()
                Log.write("Userhosts %s" % self.userhosts)                
        return True
    
    def cmd_privmsg(self, line):
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
                if usr and (self.status_flag('hear') or self._masters[usr]['auth'] == 0):    # If a valid user and hearing is enabled or user is admin
                    Thread(target=self.parse_cmd, args=(usr, m.group(1), m.group(2), str.lstrip(' '.join(line[3:]),':'),), name='parse_cmd').start()                        
        elif self.status_flag('voice'):                              
            m = self._regexes['special'].search(line[0])      # Extract user's details                                                                
            if m:              
                usr = None                          
                for k in self._masters.iterkeys():
                    if m.group(k):
                        usr = k
                        break;
                                   
                if usr:                                       # Call extended parser in separate thread                    
                    Thread(target=self.parse_msg, args=(usr, m.group(1), m.group(2), str.lstrip(' '.join(line[3:]),':'),), name='extended_parse').start()
        
        return super(ArmageddonBot, self).cmd_privmsg(line) 
    
    #Overriden events
    
    def on_bot_terminate(self):
        '''
            @summary: Called when the bot terminates
        '''
        self.save_state()                                     # Save state
        if not self.close_requested():                        # Restart was requested
            Log.write("Resurrecting...")            
            self._sock = socket.socket();
            Thread(target=self.start, name='start').start()
        else:                
            self._modmgr.module('user').remind_dispose()
            self._logger.close()
            Log.write("Boom! Owww. *Dead*")        

    #def on_connected(self):
    #    self.load_state()
                            
    def on_bot_mode_set(self):        
        '''
            @summary: Called when a mode is set on the bot.
            @note: Used to trigger commands in queue requiring OP
        '''        
        if self._flags['o']:
            if self._armastep == 3:
                self.queue_op_add(target=self.armageddon)                    
            Thread(target=self.queue_op_process, name='QircBot.queue_op_process').start() 
      
    #Persistence
    def save_state(self):
        '''
            @summary: Saves the state of the bot and the modules
        '''
        pickler = cPickle.Pickler(open('Qirc.pkl', 'wb'))        
        pickler.dump(self._masters)        
        pickler.dump(self._arma_resetlist)
        pickler.dump(self._modmgr.get_state())      # Dump Modules
        pickler.dump(self._cmdmgr.get_state())      # Dump Command Modules
        pickler.dump(self._logger.get_state())      # Logger
        
    
    def load_state(self):
        '''
            @summary: Loads the state of the bot and the modules
        '''
        if path.exists('Qirc.pkl'):            
            pickler = cPickle.Unpickler(open('Qirc.pkl', 'rb'))
            try:
                self._masters = pickler.load()
                self._arma_resetlist = pickler.load()                                
                self._modmgr.set_state(pickler.load())
                self._cmdmgr.set_state(pickler.load())
                self._logger.set_state(pickler.load())
            except:
                Log.error('Bad pickle state: ')
        
    # Implementation of parsers  
    def parse_cmd(self, role, nick, host, cmd):
        '''
            @var role: The group of user
            @var nick: Nick of user
            @var host: Hostname of user
            @var cmd: Command from standard input
            @summary: Parses the command from PM to bot
        '''                
        m = self._regexes['cmd'].search(cmd)
        if m:            
            if self._masters[role]['powers'] is None or m.group(1) in self._masters[role]['powers']:
                if m.group(1) == 'help':
                    if self._masters[role]['powers'] is None:
                        self.notice(nick, 'Commands are: help, join, quit, flags, enforce, op, say, kick, ban, armageddon')
                    else:
                        self.notice(nick, 'Commands are: %s' % ', '.join(self._masters[role]['powers']))
                else:
                    (_, result, success) = self._cmdmgr.parse(nick, host, self._masters[role]['auth'], self._masters[role]['powers'], m.group(1), m.group(2) if m.group(2) else '')
                    if success is None:
                        if self._masters[role]['powers'] is None:
                            self.send(cmd)
                    if success:
                        if result:
                            return False                                                    
                    elif result:
                        self.send_multiline(self.notice, nick, result.output)

            else:
                self.notice(nick, 'You are not authorized to perform this operation. Type /msg %s help to see your list of commands' % self.params['nick'])
        return True
       
    def parse_msg(self, role, nick, host, msg):
        '''
            @var role: The group of user
            @var nick: Nick of user
            @var host: Hostname of user
            @var msg: Message for bot
            @summary: Specifies additional rules as the general purpose responses
        '''
        Log.write("Parse Message %s" % msg)    
        self._modmgr.module('url').append_if_url(msg)                   # Check for URL
        
        # Tell Messages
        messages = self._modmgr.module('user').tell_get(nick)
        if messages:
            for sender, msg in messages:
                self.say('%s, %s said "%s"' % (nick, sender, msg))
                
        # Voting
        if self._modmgr.module('vote').is_voting:
            if len(msg) == 1:
                self._modmgr.module('vote').register_vote(nick, host, msg)
                return True
        if self._modmgr.module('game').is_joining:
            if msg == "+":
                self._modmgr.module('game').join(nick)
                return True
        elif self._modmgr.module('game').is_playing:
            self._modmgr.module('game').response(nick, msg)            
            return True
               
        m = self._regexes['module-cmd'].search(msg)        
        if m:    
            if m.group(1) == 'help':                
                self.send_multiline(self.notice, nick, """Enter <command> -h for help on the respective command
Commands: 
    !help             Shows this help
    !search, !s, !g   Search for a term on various sites
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
            else:
                (_, result, success) = self._modmgr.parse(nick, host, self._masters[role]['auth'], self._masters[role]['powers'], m.group(1), m.group(2) if m.group(2) else '')
                if not success:
                    if result:
                        self.send_multiline(self.notice, nick, result.output)                                                    
                elif result:
                    self.say(result.output)        
        else:
            m = self._regexes['module-reply'].search(msg)
            if m and self.status_flag('talk'):
                self._modmgr.reply(nick, host, self._masters[role]['auth'], self._masters[role]['powers'], m.group(1)) 
      
    def user_list(self):
        '''
            @summary: Returns the list of masters as a dict
        '''
        d = {}
        for k, v in self._masters.items():
            if k != "others":
                d[k] = v['members']
        return d.items()
    
    def power_list(self):
        '''
            @summary: Returns the list of groups and their powers as a dict
        '''
        d = {}
        for k, v in self._masters.items():
            if k != "others":
                d[k] = v['powers']
        return d.items()
     
    def role_power(self, role, power, remove=False):
        '''
            @var role: The group of user
            @var hostname: The power
            @summary: Adds/Removes the power of a group
        '''
        if self._masters.has_key(role):
            if remove:
                if power in self._masters[role]['powers']:
                    self._masters[role]['powers'].remove(power)
                    return True
            elif power not in self._masters[role]['powers']:
                self._masters[role]['powers'].append(power)
                return True
               
    def user_add(self, role, hostname):
        '''
            @var role: The group of user
            @var hostname: The hostname of user
            @summary: Adds the hostname to a specified group of masters
        '''
        if self._masters.has_key(role):
            if hostname not in self._masters[role]['members']:
                self._masters[role]['members'].append(hostname)
                self.regex_prepare_users()
                return True
    
    def user_remove(self, role, hostname):
        '''
            @var role: The group of user
            @var hostname: The hostname of user
            @summary: Removes the hostname from a specified group of masters
        '''
        if self._masters.has_key(role):
            if hostname in self._masters[role]['members']:
                self._masters[role]['members'].remove(hostname)
                self.regex_prepare_users()
                return True
            
    def user_auth(self, user=None, role=None):
        '''
            @var user: The user's hostmask
            @var role: The group name
            @summary: Returns the authority level of the user or group
        '''
        if user:
            for v in self._masters.values():
                if user in v['members']:
                    return v['auth']
        elif role:
            if self._masters.has_key(role):
                return self._masters[role]['auth']        
                    
    # WARNING: Do you know what you are doing?
    def arma_whitelist(self):
        return self._cmdmgr.module('armageddon').whitelist()
    
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
            self.op(self.current_channel, self.params['nick'])  
        else:                                           # Final Stage, kickban everyone except in whitelist
            self._armastep = 0                          # Reset armageddon to Stage 0
            self._arma_resetlist = []
            regx = re.compile(r'^[^@]*@(%s)' % '|'.join(self.arma_whitelist())) # Set whitelist
            self._arma_whitelist = [] 
            for u,h in self.userhosts.iteritems():                                         
                if  regx.match(h) is None:                                        
                    Log.write('armageddon-kickban %s %s' % (u, h))
                    self.ban('*!' + h, False)
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
            self.op(self.current_channel, self.params['nick'])  
                    
    def chunk(self,l, n):
        '''
            @var l: The list to chunk
            @var n: Number of elements per chunk
            @summary: Splits a list into chunks having n elements each
        '''
        return [l[i:i+n] for i in range(0, len(l), n)]
    


# Use the final Bot as QircBot
QircBot = ArmageddonBot