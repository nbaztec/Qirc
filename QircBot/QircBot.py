'''
Created on Jun 7, 2012
Updated on Oct 16, 2012
@author: Nisheeth
@version: 4.0.1 Ethereal
'''

from Modules.Manager import DynamicExtensionManager, DynamicCommandManager
from Modules import External, Internal, Commands
        
from QircDatabase import SqliteDb
from Util.Log import Log
from Util.ThreadQueue import ThreadQueue
from Util.Common import chunk
from abc import ABCMeta, abstractmethod
from threading import Thread, Lock, Condition
       
from os import path
import random
import re
import socket
import select
import time
import cPickle
import inspect

class User(object):
        
    regex_normal = re.compile(r'^([^!]+)!([^@]+)@(.*)$')
    
    @classmethod
    def set_special_regex(cls, regex):
        cls.regex_special = regex
        
    @classmethod
    def set_normal_regex(cls, regex):
        cls.regex_normal = regex
                        
    def __init__(self, *args, **kwargs):        
        d = {
               'masters': None,
               'simple' : False,
               'server' : False
            }
        d.update(kwargs)
        
        if len(args) == 6:            
            self._nick = args[0]
            self._ident = args[1]
            self._host = args[2]
            self._role = args[3]
            self._auth = args[4]
            self._powers = args[5]
        elif len(args) == 1:
            self._nick = None
            self._ident = None
            self._host = None
            self._role = None
            self._auth = None
            self._powers = None
            
            self._input = username = args[0]            
            masters = d['masters']
            simple = d['simple']
            server = d['server']
            if server:
                if username:
                    self._nick = username
                    self._host = self._ident = ''                
            elif username: 
                m = None
                
                if not simple and User.regex_special:
                    m = User.regex_special.search(username)
                
                if m is None:
                    if User.regex_normal:
                        m = User.regex_normal.search(username)
                        if m:
                            self._nick  = m.group(1)
                            self._ident = m.group(2)
                            self._host  = m.group(3)
                else:                        
                    self._nick  = m.group(1)
                    self._ident = m.group(2)
                    self._host  = m.group(3)
                    
                    if masters:
                        role = 'others'            
                        for k in masters.iterkeys():
                            if m.group(k):
                                role = k
                                break;                                                
                        
                        self._role  = role 
                        self._auth  = masters[role]['auth']
                        self._powers  = masters[role]['powers']
        else:
            raise Exception("Incorrect number of arguments")
    
    def __str__(self):
        if self._nick and self._ident and self._host:
            return '%s!%s@%s' % (self._nick, self._ident, self._host)
        return self._input
    
    @property
    def nick(self):
        return self._nick
    
    @property
    def ident(self):
        return self._ident
    
    @property
    def host(self):
        return self._host
    
    @property
    def role(self):
        return self._role
    
    @property
    def auth(self):
        return self._auth
    
    @property
    def powers(self):
        return self._powers


class BaseBot(object):
    '''
        The abstract class BaseBot manages the base working of the bot as well as the interface.
        @version: 3.0
    '''
    
    __metaclass__ = ABCMeta
        
    def __init__(self, callback, params=None):
        '''
            @param callback  : A callback function to be called when bot is successfully registered
            @param params    : Parameters for the bot,
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
              'password'    : None,
              'chan'        : []           
              }
        if params is not None:            
            self.params.update(params)            
        Log.write(self.params)
        
        self._regexes = { }
        
        self._sock = socket.socket();
        self._success_callback = callback     
        self._lock = Lock()                     # mutex _lock [unused]                
        self.orig_nick = self.params['nick']    # Store original nick for temp logins        
        
        self._cv_exit = Condition()
        
        BaseBot.reset_flags(self)               # Reset bot state
        
    def reset_flags(self, build=True):
        '''
            @param build: If true, then status_flags are initialized 
            @summary: Resets the state flags of the bot 
        '''
        self._retry_timeout = 15                # 15 seconds connection retry                               
        self._restart_req = self._has_quit = False                  # If a QUIT request was sent by the master
        if build:       
            self._status_flags = {
                              'hear'    : True,
                              'voice'   : True,                              
                              'kick'    : True,
                              'ban'     : True,
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
    
    def restart_requested(self):
        '''
            @summary: Whether a valid restartrequested was placed or not
        '''
        return self._restart_req
                           
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
            self._sock.setblocking(0)            
            self._retry_timeout = 15
            return True
        except socket.error, e:
            Log.write('Failed to connect %s Reconnecting in %d seconds' % (e, self._retry_timeout))
            time.sleep(self._retry_timeout)
            if self._retry_timeout < 180:
                self._retry_timeout *= 1.5                      # Increase retry time after every failure
            else:
                self._retry_timeout = 180                       # Limit retry time to 3 minutes
    
    def register(self):
        '''
            @summary: Registers the bot on IRC
        '''
        self.send("NICK %s" % self.params['nick'])
        self.send("USER %s %s bla :%s" % (self.params['ident'], self.params['host'], self.params['realname']))
    
    def send(self, msg):
        '''
            @param msg: Message to send
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
            @summary: Synchronous reading via selecting 
        '''        
        try:
            self._read_buffer = ''
            run_read = True
            chunk = '+'                             # Initially chunk not empty
            while run_read and not self.close_requested() and not self.restart_requested():
                if select.select([self._sock], [], [], 10)[0]:
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
            @param recv: Message from IRC
            @summary: Parses the messages coming from the IRC to take suitable actions
        '''
        pass        

          
class ActiveBot(BaseBot):
    '''
        ActiveBot allows the bot to perform simple commands and operations.
        @version: 4.0
    '''
    
    def __init__(self, callback, params=None):
        '''
            @param callback  : A callback function to be called when bot is successfully registered
            @param params    : Parameters for the bot,
                             Default:
                                  'host'        : 'irc.freenode.net'
                                  'port'        : 6667
                                  'nick'        : 'QircBot'
                                  'ident'       : 'QircBot'
                                  'realname'    : 'QirckyBot'  
                                  'password'    : None                             
        '''
        super(ActiveBot, self).__init__(callback, params)
        ActiveBot.reset_flags(self, False)                 # Initialize flags but do not bubble up, since already set by BaseBot.__init__()
         
        self._op_actions = ThreadQueue()                   # ThreadQueue for OP functions
        self._multisend_lock = Lock()                      # Thread lock for avoiding floodkicks on send_multiline()
        self._cv_userlist = Condition()                    # Condition Variable for requesting userlist                
    
    def current_userlist(self):
        '''
            @summary: Returns the userlist for the current channel
        '''
        return self._names
    
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
            @param bubble: Whether to reset the flags in the base class
            @summary: Resets the state flags of the bot 
        '''
        self._alive = True
        self._joined = False
        self._pong_recv = True
        self._ghost = False
        self._names = {}
        if bubble:
            BaseBot.reset_flags(self)
        
    def cleanup(self):
        '''
            @summary: Performs any cleanup activity while qutting the bot
        '''        
        BaseBot.cleanup(self)    
    
    def request_userlist(self):
        '''
            @summary: Activates a request for raising `userlist` event
        '''
        self._cv_userlist.acquire()
        self._request_userlist = True
        self._cv_userlist.notify()
        self._cv_userlist.release()
    
    def userlist_buildup(self):
        '''
            @summary: Builds a {nick : username} dict for all the members in current channel at periodic intervals
        '''                
        try:            
            self._cv_userlist.acquire()
            self._cv_userlist.wait()        # Wait for signal to proceed
            self._cv_userlist.release()
            time.sleep(10)                  # Delay 10 seconds to receive NAMES
        except:
            pass
            
        self._request_userlist = False
        userlist_pending = userlist_req = False
        while self._alive and not self.close_requested() and not self.restart_requested():
            try:                                                
                userlist_req = False
                l = []                                                      # Check if any nick doesn't have the username entry
                for k,v in self._names.items():
                    if v is None:
                        l.append(k)
                if len(l):                                                  # Request hostnames of empty nicks
                    userlist_req = userlist_pending = True
                    for n in chunk(l, 5):
                        self.userhosts(' '.join(n))                    
                #else:                    
                    Log.write('Userlist: %s' % self._names, 'D')
                
                self._cv_userlist.acquire()
                if userlist_req:                    
                    if self._request_userlist:
                        self._cv_userlist.wait(5)                           # Recheck after 5 seconds if list is requested
                    else:
                        self._cv_userlist.wait(10)                          # Recheck after 30 seconds otherwise
                elif userlist_pending or self._request_userlist:
                    self._request_userlist = userlist_pending = False                    
                    self.on_userlist_complete()                    
                    self._cv_userlist.wait(60)                              # Sleep for 60 seconds
                else:                    
                    self._cv_userlist.wait(60)                              # Sleep for 60 seconds
                self._cv_userlist.release()                    
            except Exception, e:
                Log.error(e)
                                        
            
    def server_ping(self):        
        '''
            @summary: Pings the server every 90 seconds to keep the connection alive
        '''
        while self._pong_recv and not self.close_requested() and not self.restart_requested():           # If PONG was received for the previous PING, if not the connection is probably dead            
            self._pong_recv = False
            try:                        
                self._cv_exit.acquire()
                self._cv_exit.wait(60)                                  # PING every 60 seconds
                self._cv_exit.release()                
                        
                if not self.close_requested() and not self.restart_requested():
                    self.ping()                                         # Send PING                
                    self._cv_exit.acquire()
                    self._cv_exit.wait(30)                              # Wait 30 seconds for a PONG
                    self._cv_exit.release()                 
            except:
                pass
        
        self._alive = False
        if not self.close_requested() and not self.restart_requested():
            self._cv_exit.acquire()
            self._cv_exit.notify_all()
            self._cv_exit.release()
        '''
        try:
            self.ping()                                                     # Precautionary PING to unblock the socket.recv()
        except:
            pass
        '''
        Log.write('Server Failed to respond to PONG', 'E')
            
    def queue_op_add(self, target, args=(), kwargs={}):
        '''
            @param target: The function
            @param args: Arguments to function
            @param kwargs: Keyworded arguments to function
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
            self._op_actions.process()                              # Process
            self._op_actions.join()                                 # Block until complete
            self.deop(self.current_channel, self.params['nick'])
            self._flags['o'] = False                                # Precautionary measure
        self._lock.release()
            
    def get_flag(self, key=None):
        '''
            @param key: Key of the flag, None if all flags are required
            @return: Returns flag status else all flags            
        '''
        if key is None:
            return self._flags.items()
        elif self._flags.has_key(key):            
            return self._flags[key]
        else:
            return False
    
    def set_flags(self, key=None, value=None, flag_dict=False):
        '''
            @param key: Key to flags
            @param value: The new value to set, if required 
            @param flag_dict: If true, then the entire dict is set/returned
            @return: Returns True if the status is set, else False
        '''
        if flag_dict:
            if value is None:
                return self._flags
            else:        
                self._flags = value
        else:
            if key is None:
                return self._flags.items()
            else:
                if value is not None:
                    self._flags[key] = value
                    return value
                elif self._flags.has_key(key):            
                    return self._flags[key]
                else:
                    return False
        
    def get_status(self, key=None):
        '''
            @param key: Key of the status, None if all statuses are required
            @return: Returns status else all statuses
            @note: This is a read-only variant of set_status()
        '''
        if key is None:
            return self._status_flags.items()
        elif self._status_flags.has_key(key):            
            return self._status_flags[key]
        else:
            return False
            
    def set_status(self, key=None, value=None, flag_dict=False):
        '''
            @param key: Key to status
            @param value: The new value to set, if required 
            @param flag_dict: If true, then the entire dict is set/returned
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
                elif self._status_flags.has_key(key):            
                    return self._status_flags[key]
                else:
                    return False
                
    # Shortcut Functions
    
    def ping(self):
        '''
            @summary: Sends a PING message to the server 
        '''
        self.send("PING %s" % self.params['host'])
        
    def join(self, chan, key=''):
        '''
            @param chan: The channel to join. Example #chan
            @summary: Sends a JOIN command to join the channel and updates the current channel
        '''                
        self.send('JOIN %s %s' % (chan, key))
        
    def part(self, chan, msg=''):
        '''
            @param msg: PART message
            @summary: Parts the bot from a channel
        '''
        self.send("PART %s :%s" % (chan, msg))        
        
    def identify(self):
        '''
            @summary: Sends a message to identify bot's NICK 
        '''
        if self.params['password']:
            self.send("PRIVMSG nickserv :identify %s" % self.params['password'])
        
    def ghost(self, nick):
        '''
            @param nick: NICK to ghost
            @summary: Sends a message to NickServ to ghost a NICK
        '''
        if self.params['password']:
            Log.write("Ghosting nick...")
            self.send("PRIVMSG nickserv :ghost %s %s" % (nick, self.params['password']))        
    
    def nick(self, nick):
        '''
            @param nick: New nick for bot
            @summary: Sends a NICK message to to change bot's nick
        '''
        self.send("NICK %s" % nick)    
        
    def disconnect(self, msg):
        '''
            @param msg: QUIT message
            @summary: Disconnect the bot from the IRC
        '''
        self.send('QUIT :%s' % msg)         
    
    def say(self, msg):     
        '''
            @param msg: Message to say
            @summary: Say something in the current channel
        '''   
        self.send('PRIVMSG %s :%s' % (self.current_channel, msg))
        
    def msg(self, nick, msg):
        '''
            @param nick: User nick or channel
            @param msg: Message to say
            @summary: Say something to a channel or user
        '''   
        self.send('PRIVMSG %s :%s' % (nick, msg))
    
    def notice(self, nick, msg):
        '''
            @param nick: User nick or channel
            @param msg: Message to say
            @summary: Whisper something to a channel or user
        '''   
        self.send('NOTICE %s :%s' % (nick, msg))
            
    def send_multiline(self, method, nick, lines):
        '''
            @param method: The method to use to send the message
            @param nick: The user to send the message to, if applicable
            @param lines: A multiline message string
        '''             
        for line in lines.split('\n'):
            self._multisend_lock.acquire()
            if nick:
                method(nick, line)
            else:
                method(line)      
            
            try:              
                time.sleep(0.5)
            except:
                pass
            
            self._multisend_lock.release()
            
    def kick(self, nick, msg, auto_op=True):        
        '''
            @param nick: User nick
            @param msg: KICK reason
            @param auto_op: If set to true ensures that the bot is +o'd first
            @summary: Kicks a user from the channel
            @attention: Requires OP mode
        '''
        if self.get_status('kick') and nick != self.params['nick']:     # Avoid kicking self
            if self._flags['o']:
                self.send('KICK %s %s %s' % (self.current_channel, nick, ' :'+msg if msg else ''))
            elif auto_op:
                self.queue_op_add(target=self.kick, args=(nick, msg, False,))
                self.op(self.current_channel, self.params['nick'])
    
    def ban(self, host, auto_op=True):
        '''
            @param host: User's hostmask
            @param auto_op: If set to true ensures that the bot is +o'd first
            @summary: Bans a user from the channel
            @attention: Requires OP mode
        '''
        if self.get_status('ban') and host.lstrip("*!*@") != self._names[self.params['nick']].host:
            if self._flags['o']:
                self.send('MODE %s +b %s' % (self.current_channel, host,))
            elif auto_op:
                self.queue_op_add(target=self.ban, args=(host, False,))    
                self.op(self.current_channel, self.params['nick'])        
    
    def kickban(self, nick, host, msg, auto_op=True):        
        '''
            @param nick: User nick
            @param msg: KICK reason
            @param auto_op: If set to true ensures that the bot is +o'd first
            @summary: Kicks a user from the channel
            @attention: Requires OP mode
        '''        
        if self.get_status('kick') and self.get_status('ban') and nick != self.params['nick']:     # Avoid kicking self
            if self._flags['o']:
                self.kick(nick, msg)
                self.ban(host)
            elif auto_op:
                self.queue_op_add(target=self.kickban, args=(nick, host, msg, False,))
                self.op(self.current_channel, self.params['nick'])
                
    def unban(self, host, auto_op=True):    
        '''
            @param host: User's hostmask
            @param auto_op: If set to true ensures that the bot is +o'd first
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
    
    def userhosts(self, names):
        '''
            @param names: Space separated string of upto 5 nicks
            @summary: Send a USERHOST command to get the list of upto 5 userhosts in the current channel
        '''       
        self.send("USERHOST %s" % names)
        
    def action(self, msg):
        '''
            @param msg: Message to display
            @summary: Send an ACTION message
        '''
        self.send("PRIVMSG %s :\x01ACTION %s\x01" % (self.current_channel, msg))
    
    def op(self, chan, nick):
        '''
            @param nick: Nick of the user to op
            @param chan: The channel to op to
            @summary: OPs the user in a given channel
        '''
        self.send("PRIVMSG ChanServ :op %s %s" % (chan, nick))
        
    def deop(self, chan, nick):
        '''
            @param nick: Nick of the user to deop
            @param chan: The channel to deop from
            @summary: DEOPs the user in a given channel
        '''
        self.send("PRIVMSG ChanServ :deop %s %s" % (chan, nick))                    
    
    def parse_recv(self, recv):
        '''
            @param recv: Messages from IRC
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
            @param line: The text received broken into tokens
            @summary: Ping was received            
        '''
        self.send("PONG %s" % line[1])
        return self.recv_ping(line[1].lstrip(':')) 
    
    def cmd_pong(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: Pong was received            
        ''' 
        self._pong_recv = True
        return self.recv_pong(line[0].lstrip(':'), line[-1].lstrip(':'))
    
    def cmd_quit(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: QUIT was received            
        '''
        return self.recv_quit(line[0].lstrip(':'), ' '.join(line[2:]).lstrip(':'))
        
        
    def cmd_part(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: PART was received            
        '''
        return self.recv_part(line[0].lstrip(':'), line[2], ' '.join(line[3:]).lstrip(':'))
    
    def cmd_join(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: JOIN was received            
        '''    
        return self.recv_join(line[0].lstrip(':'), line[2])
    
    def cmd_kick(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: KICK was received            
        '''
        return self.recv_kick(line[0].lstrip(':'), line[2], line[3], ' '.join(line[4:]).lstrip(':'))
    
    def cmd_notice(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: NOTICE was received            
        '''
        return self.recv_notice(line[0].lstrip(':'), line[2] == "*", ' '.join(line[3:]).lstrip(':'))        
    
    def cmd_nick(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: NICK was received            
        '''
        return self.recv_nick(line[0].lstrip(':'), line[2].lstrip(':'))
    
    def cmd_mode(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: MODE was received            
        '''         
        flags = line[3]
        
        if len(line) == 4:          # Flag on channel
            users = None
            mode = flags[0]
            flags = flags[1:]
        else:
            users = line[4:]
            mode = flags[0]
            if mode == ":":
                mode = flags[1:2]           
                flags = flags[2:]
            else:                  
                flags = flags[1:]
                
        return self.recv_mode(line[0].lstrip(':'), line[2], mode, flags, users)       
    
    def cmd_privmsg(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: PRIVMSG is received            
        '''        
        return self.recv_privmsg(line[0].lstrip(':'), line[2], ' '.join(line[3:]).lstrip(':')) 
           
    # Control Messages
    def stat_nickuse(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: The nick is already in use            
        '''                
        if not self._joined:
            self.params['nick'] = self.orig_nick + str(random.randrange(1,65535)) 
            Log.write('Retrying with nick %s' % self.params['nick'])
            self._ghost = self.params['password'] is not None   # Ghost other user/bot if password is specified
            Log.write("GHOST %s" % self._ghost)
            self.register()                                     # Retry registering
        return True
    
    def stat_startmotd(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: Start of MOTD            
        '''
        return True
    
    def stat_motd(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: Content of MOTD            
        '''
        return True
    
    def stat_endmotd(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: End of MOTD            
        '''
        if self._ghost:                             # If ghosting requested
            self.ghost(self.orig_nick)                    
            self._ghost = False
        else:
            self.identify()                         # Normal join, just identify
            Thread(target=self._success_callback, args=(self,), name='callback').start()        # Call callback function
        
        self.reset_flags(build=False)               # Give bot a fresh start
                            
        return True
    
    def stat_names(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: NAMES is received
        '''
        for x in line[5:]:
            self._names[x.strip(':@+')] = None      # Add names to current list
        return True
    
    def stat_endnames(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: End of NAMES            
        '''        
        return True        
    
    def stat_userhost(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: USERHOST is received          
        '''
        for uh in line[3:]:                                     # Build usernames
            m = self._regexes['userhost'].search(uh)
            if m:
                nick = m.group(1).lstrip(':@+')
                self._names[nick] = User(nick + '!' + m.group(2))
                self.on_recv_userhosts(nick, m.group(2))
        return True
        
    def stat_already_registered(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: ERR_ALREADYREGISTERED is received          
        '''
        self.identify()                         # Normal join, just identify
        return True   
        #return self.stat_endmotd(line)
    
    def recv_ping(self, server):
        '''
            @param server: The server that sent PING
        '''
        return True
    
    def recv_pong(self, server, msg):
        '''
            @param server: The server that sent the PONG
            @param channel: PONG message
        '''
        return True  
        
    def recv_quit(self, user, reason):
        '''
            @param user: The user that parted
            @param reason: The reason for quit
        '''                    
        u = User(user, simple=True)
        if self._names.has_key(u.nick):
            self._names.pop(u.nick)
        self.on_userlist_update()        
        if u.nick == self.params['nick']:                    
            if reason == "Disconnected by services":   # If bot is disconnected by services then do not retry [GHOSTING]
                self.close()                                                      
            return False                                  # Terminate read thread
        else:
            return True
    
    def recv_part(self, user, channel, reason):
        '''
            @param user: The user that parted
            @param channel: The channel that was parted from
        '''        
        u = User(user, simple=True)
        if self._names.has_key(u.nick):
            self._names.pop(u.nick)    
        self.on_userlist_update()
        if u.nick == self.params['nick']:
            self.on_bot_part(channel)
        return True
    
    def recv_join(self, user, channel ):
        '''
            @param user: The user that joined
            @param channel: The channel that was joined to
        '''        
        u = User(user, simple=True)
        if self._names.has_key(u.nick):
            self._names[u.nick] = u        
        self.on_userlist_update()
        if u.nick == self.params['nick']:
            self._names = {}
            self.on_bot_join(channel)
            self._cv_userlist.acquire()
            self._cv_userlist.notify_all()
            self._cv_userlist.release()
        return True
    
    def recv_kick(self, source, channel, user, reason):
        '''
            @param source: The user who issued the KICK
            @param channel: The channel on which KICK was issued
            @param user: The user who got kicked
            @param reason: The reason for kicking 
        '''
        if self._names.has_key(user):
            self._names.pop(user)
        self.on_userlist_update()
        if user == self.params['nick']:                         # If bot is kicked
            self.join(channel)
        return True
    
    def recv_notice(self, source, broadcast, msg):
        '''
            @param source: The source of the NOTICE
            @param broadcast: True if the notice is a broadcasted notice 
            @param msg: The message received
        '''
        if msg.find(' has been ghosted') != -1:                 # Duplicate NICK has been ghosted
            self.nick(self.orig_nick)                           # Claim original NICK
            self.identify()                                     # Identify
            Thread(target=self._success_callback, args=(self,), name='callback').start()        # Call callback function
        return True
    
    def recv_nick(self, user, new_nick):
        '''
            @param user: The user who issued NICK
            @param new_nick: The new NICK
        '''                
        u = User(user, simple=True)
        if self._names.has_key(u.nick):
            self._names.pop(u.nick)
            self._names[new_nick] = u
        self.on_userlist_update()        
        if u.nick == self.params['nick']:
            self.params['nick'] = new_nick
            self.on_bot_nick_change(self.params['nick'])
            self.call_listeners('botnick', None, u, self.params['nick'])            
        return True
    
    def recv_mode(self, source, channel, mode, flags, users):
        '''
            @param source: The user who issued the KICK
            @param channel: The channel on which KICK was issued
            @param mode: Flags set or reset (+ or -)
            @param flags: The flags issued
            @param users: The users specified
        '''        
        if users and self.params['nick'] in users:    # Mode is set on an user and not on channel (hence the 4th index)                  
            for c in flags:
                self._flags[c] = (mode == '+')            
            
            if mode == '+':
                self.on_bot_mode_set()
            else:
                self.on_bot_mode_reset()
        return True
    
    def recv_privmsg(self, user, channel, msg):
        '''
            @param source: The user sending the PRIVMSG
            @param source: The message received
        '''            
        return True
            
    def on_connected(self):
        '''
            @summary: Called when the bot is connected
        '''
        self._has_quit = self._restart_req = False
        Thread(target=self.server_ping, name='ActiveBot.server_ping').start()               # Start pinger thread
        Thread(target=self.userlist_buildup, name='ActiveBot.userlist_buildup').start()     # Start userlist monitoring thread
    
    def on_bot_join(self, channel):
        '''
            @param channel: The channel name
            @summary: Called when the bot joins a channel
        '''          
        if channel not in self.params['chan']: 
            self.params['chan'].insert(0, channel)     # Reset  channel from state, if parted
    
    def on_bot_part(self, channel):
        '''
            @param channel: The channel name
            @summary: Called when the bot parts the channel
        '''        
        if channel in self.params['chan']: 
            self.params['chan'].remove(channel)     # Reset  channel from state, if parted
    
    def on_bot_mode_set(self):
        '''
            @summary: Called when a mode is set on the bot
        '''
        if self._flags['o']:
            Thread(target=self.queue_op_process, name='QircBot.queue_op_process').start() 
        pass
    
    def on_bot_mode_reset(self):
        '''
            @summary: Called when a mode is reset on the bot
        '''
        pass

    def on_bot_nick_change(self, nick):
        '''
            @param nick: The new nick
            @summary: Called when the nick is changed on bot
        '''
        pass
    
    def on_recv_userhosts(self, nick, userhost):
        '''
            @param nick: The nick
            @param userhost: The nick's userhost
            @summary: Called when the a userhost is received
        '''
        pass
    
    def on_userlist_complete(self):
        '''            
            @summary: Called when the the userlist has all entries completed
        '''
        pass
    
    def on_userlist_update(self):
        '''            
            @summary: Called when the the userlist is changed
        '''
        pass
    
class ArmageddonBot(ActiveBot):
    '''
        @summary: Incorporates complex functionality into the bot
        @version: 4.0
    '''    
    
    def __init__(self, callback, params=None):
        '''
            @param callback  : A callback function to be called when bot is successfully registered
            @param params    : Parameters for the bot,
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
                        
        self._qircdb = SqliteDb()
        
        # Module Managers
        self._extmgr = DynamicExtensionManager()   
        self._cmdmgr = DynamicCommandManager()
        
        # Load State
        self.load_state()
        
        # Load Modules
        self.load_commands()
        self.load_extensions()
        
        # Prepare Regexes                       
        self._regexes['userhost'] = re.compile(r'([^=]*)=[+-](.*$)')

        self.regex_prepare_users()
        
    def regex_prepare_users(self):
        '''
            @summary: Prepare a list of master and compiles the regex
        '''
        self._special_users = []                        # Prepare special list of users for optimizing match timings
        for k, v in self._masters.items():
            if k != 'others':                           # Ensure others is last
                self._special_users.append('(?P<%s>%s)' % (k, '|'.join(v['members'])))
        self._special_users.append('(?P<%s>%s)' % ('others', '|'.join(self._masters['others']['members'])))
        self._regexes['special'] = re.compile(r'^([^!]+)!(~*[^@]+)@(%s)$' % '|'.join(self._special_users))         # Regex for matching hostmask of users
        
        User.set_special_regex(self._regexes['special'])
        
    def load_commands(self):
        '''
            @param reload_cmds: True if the modules have to be reloaded, False otherwise
            @summary: Loads modules dynamically into the bot 
        '''
        for module_file in [Commands]:            
            Log.write('Reloading %s' % module_file.__name__)
            reload(module_file)                        
            Log.write('Importing Commands in %s ' % module_file.__name__)
            for name, obj in inspect.getmembers(module_file, predicate=inspect.isclass):
                if inspect.isclass(obj) and obj.__bases__[0].__name__ == "BaseDynamicCommand":
                    Log.write('Importing : %s' % name)
                    if self._cmdmgr.add(obj(self), False):
                        Log.write('[!] %s replaced previous command with same key' % name)
            self._cmdmgr.build_regex()
                                    
        self._cmdmgr.reload()       # Call reload on every module
        return True
            
    def load_command(self, key):
        '''
            @param key: A string identifying the module to load
            @summary: Loads a command dynamically into the bot  
        '''
        for module_file in [Commands]:            
            Log.write('Reloading %s' % module_file.__name__)
            reload(module_file)                        
            Log.write('Importing Command in %s ' % module_file.__name__)
            for name, obj in inspect.getmembers(module_file, predicate=inspect.isclass):
                if inspect.isclass(obj) and obj.__bases__[0].__name__ == "BaseDynamicCommand":
                    if obj(self).key == key:
                        Log.write('Importing : %s' % name)
                        self._cmdmgr.add(obj(self), False)
                        self._cmdmgr.build_regex()
                        self._cmdmgr.reload(key)
                        return True
            return False
    
    def load_extensions(self, ext_type=0):
        '''
            @param reload_mods: True if the modules have to be reloaded, False otherwise
            @summary: Loads modules dynamically into the bot 
        '''
        
        if ext_type == 0:
            modules = [Internal, External]
        elif ext_type == 1:
            modules = [Internal]
        elif ext_type == 2:
            modules = [External]
            
        for module_file in modules:            
            Log.write('Reloading %s' % module_file.__name__)
            reload(module_file)                        
            Log.write('Importing Extensions in %s ' % module_file.__name__)
            for name, obj in inspect.getmembers(module_file, predicate=inspect.isclass):
                if inspect.isclass(obj) and obj.__bases__[0].__name__ == "BaseDynamicExtension":
                    Log.write('Importing : %s' % name)
                    if self._extmgr.add(obj(self), False):
                        Log.write('[!] %s replaced previous extension with same key' % name)
            self._extmgr.build_regex()
                                    
        self._extmgr.reload()       # Call reload on every module
        return True
        
    def load_extension(self, key, ext_type=0):
        '''
            @param key: A string identifying the module to load
            @summary: Loads a module dynamically into the bot 
        '''
        if ext_type == 0:
            modules = [Internal, External]
        elif ext_type == 1:
            modules = [Internal]
        elif ext_type == 2:
            modules = [External]
            
        for module_file in modules:            
            Log.write('Reloading %s' % module_file.__name__)
            reload(module_file)                        
            Log.write('Importing Extension in %s ' % module_file.__name__)
            for name, obj in inspect.getmembers(module_file, predicate=inspect.isclass):
                if inspect.isclass(obj) and obj.__bases__[0].__name__ == "BaseDynamicExtension":
                    if obj(self).key == key:
                        Log.write('Importing : %s' % name)
                        self._extmgr.add(obj(self), False)
                        self._extmgr.build_regex()
                        self._extmgr.reload(key)
                        return True
            return False
    
    def reload_commands(self, key=None):
        '''
            @summary: Reload the current modules of the bot
        '''
        if key is None:
            state = self._cmdmgr.get_state()
            self.call_listeners('reload', None, None, None, only=['cmd'])
            self._cmdmgr.clear()
            self._cmdmgr.set_state(state)
            return self.load_commands()            
        else:
            state = self._cmdmgr.get_current_module_state(key)
            self._cmdmgr.call_listener('reload', key, None, None, None)
            if self._cmdmgr.remove(key):
                self._cmdmgr.set_module_state(key, state)
                return self.load_command(key)
            else:
                return False
        
    def reload_extensions(self, key=None, ext_type=0):
        '''
            @summary: Reload the current extensions of the bot
        '''
        if key is None:
            state = self._extmgr.get_state()            
            self.call_listeners('reload', None, None, None, only=['mod'])
            self._extmgr.clear()
            self._extmgr.set_state(state)
            return self.load_extensions(0)      # Reload all as clear() erases all extensions
        else:
            state = self._extmgr.get_current_module_state(key)
            self._extmgr.call_listener('reload', key, None, None, None)
            if self._extmgr.remove(key):
                self._extmgr.set_module_state(key, state)
                return self.load_extension(key, ext_type)
            else:
                return False
            
    def get_module(self, key, mgr_type=0):
        '''
            @param key: Returns a module specified by the key
            @param mgr_type: The manager to select - extension/command (0/1)
        '''
        if mgr_type == 0:
            return self._extmgr.module(key)
        elif mgr_type == 1:
            return self._cmdmgr.module(key)
        
    def get_module_keys(self, mgr_type=0, enabled=True):
        '''            
            @param mgr_type: The manager to select - extension/command (0/1)
            @param enabled: True if enabled modules have to be returned, False if disabled ones are required 
            @return: A list of module keys
        '''
        if mgr_type == 0:            
            return (self._extmgr.enabled_modules() if enabled else self._extmgr.disabled_modules()) 
        elif mgr_type == 1:
            return (self._cmdmgr.enabled_modules() if enabled else self._cmdmgr.disabled_modules())            
    
    def get_sqlite_db(self):
        '''
            @return: Get the instance of sqlite database
        '''
        return self._qircdb
    
    def get_username(self, nick):
        '''
            @param nick: User's nick
            @return: User's complete username or None
        '''
        if self._names.has_key(nick):
            return self._names[nick]
        else:
            return None
        
    def get_user_info(self, user):
        '''
            @param user: Complete username of the user
            @return: A dict object containing information about the user
        '''
        if user is None:
            return None
        m = self._regexes['special'].search(user)      # Extract user's details                                                                
        if m:              
            role = 'others'            
            for k in self._masters.iterkeys():
                if m.group(k):
                    role = k
                    break;
                                           
            return { 
                        'nick'      : m.group(1).lstrip(':@+'), 
                        'ident'     : m.group(2),
                        'host'      : m.group(3),
                        'role'      : role,
                        'auth'      : self._masters[role]['auth'],
                        'powers'    : self._masters[role]['powers']
                    }
    
    def call_listeners(self, key, channel, user, args, only=['mod', 'cmd']):
        if 'mod' in only:
            self._extmgr.call_listeners(key, channel, user, args)
        if 'cmd' in only:
            self._cmdmgr.call_listeners(key, channel, user, args)
        
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
    
    def role_list(self):
        '''
            @summary: Returns the list of groups and their auths as a dict
        '''
        d = {}
        for k, v in self._masters.items():
            if k != "others":
                d[k] = v['auth']
        return d.items()
            
    def role_power(self, role, power, remove=False):
        '''
            @param role: The group of user
            @param hostname: The power
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
     
    def role_add(self, role, auth):
        '''
            @param role: The group name
            @param auth: The authorization level of group
            @summary: Adds the group to the list of masters
        '''
        if not self._masters.has_key(role):            
            self._masters[role] = { 'members': [], 'auth': auth, 'powers': []}
            return True
    
    def role_remove(self, role):
        '''
            @param role: The group name
            @summary: Removes the group from the list of masters
        '''
        if self._masters.has_key(role):
            self._masters.pop(role)            
            return True
                      
    def user_add(self, role, hostname):
        '''
            @param role: The group of user
            @param hostname: The hostname of user
            @summary: Adds the hostname to a specified group of masters
        '''
        if self._masters.has_key(role):
            if hostname not in self._masters[role]['members']:
                self._masters[role]['members'].append(hostname)
                self.regex_prepare_users()
                return True
    
    def user_remove(self, role, hostname):
        '''
            @param role: The group of user
            @param hostname: The hostname of user
            @summary: Removes the hostname from a specified group of masters
        '''
        if self._masters.has_key(role):
            if hostname in self._masters[role]['members']:
                self._masters[role]['members'].remove(hostname)
                self.regex_prepare_users()
                return True
            
    def user_auth(self, user=None, role=None):
        '''
            @param user: The user's hostmask
            @param role: The group name
            @summary: Returns the authority level of the user or group
        '''
        if user:
            for v in self._masters.values():
                if user in v['members']:
                    return v['auth']
        elif role:
            if self._masters.has_key(role):
                return self._masters[role]['auth']     
            
    # Overriden recv methods
    def reset_flags(self, bubble=True, build=True):
        '''
            @param bubble: Whether to reset the flags in the base class
            @summary: Resets the state flags of the bot 
        '''        
        if bubble:
            super(ArmageddonBot, self).reset_flags(build)
                       
    def cmd_join(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: JOIN was received            
        '''                                
        return super(ArmageddonBot, self).cmd_join(line)
    
    def on_bot_join(self, channel):
        '''
            @param channel: The channel name
            @summary: Called when the bot joins a channel
        ''' 
        super(ArmageddonBot, self).on_bot_join(channel)
        self.names()
        self.say('All systems go!')
        
    def cmd_nick(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: NICK was received            
        '''
        return super(ArmageddonBot, self).cmd_nick(line)
    
    def recv_quit(self, user, reason):
        '''
            @param user: The user that parted
            @param reason: The reason for quit
        '''
        u = User(user, masters=self._masters)
        if u.nick == self.params['nick']:
            self.call_listeners('botquit', None, u, reason)
        else:
            self.call_listeners('quit', None, u, reason)            
        return super(ArmageddonBot, self).recv_quit(user, reason)
            
    def recv_part(self, user, channel, reason):
        '''
            @param user: The user that parted
            @param channel: The channel that was parted from
        '''        
        u = User(user, masters=self._masters)
        if u.nick != self.params['nick']:
            self.call_listeners('part', channel, u, reason)
        return super(ArmageddonBot, self).recv_part(user, channel, reason)
    
    def recv_kick(self, source, channel, user, reason):
        '''
            @param source: The user who issued the KICK
            @param channel: The channel on which KICK was issued
            @param user: The user who got kicked
            @param reason: The reason for kicking 
        '''
        if self._names.has_key(user) and self._names[user]:
            self.call_listeners('kick', channel, self._names[user], (User(source, masters=self._masters), reason))            
        return super(ArmageddonBot, self).recv_kick(source, channel, user, reason)
    
    def recv_ping(self, server):
        '''
            @param server: The server that sent PING
        '''
        self.call_listeners('pong', None, None, server)
        return super(ArmageddonBot, self).recv_ping(server)
    
    def recv_pong(self, server, msg):
        '''
            @param server: The server that sent the PONG
            @param channel: PONG message
        '''
        self.call_listeners('pong', None, None, (server, msg))
        return super(ArmageddonBot, self).recv_pong(server, msg) 
    
    def recv_join(self, user, channel):
        '''
            @param user: The user that joined
            @param channel: The channel that was joined to
        '''
        if super(ArmageddonBot, self).recv_join(user, channel):            
            self.call_listeners('join', channel, User(user, masters=self._masters), None)                
            return True
        else:
            return False
    
    def recv_notice(self, source, broadcast, msg):
        '''
            @param source: The source of the NOTICE
            @param broadcast: True if the notice is a broadcasted notice 
            @param msg: The message received
        '''
        if super(ArmageddonBot, self).recv_notice(source, broadcast, msg):
            if broadcast:
                self.call_listeners('broadcast', None, User(source, server=True), msg)
            else:
                self.call_listeners('notice', None, User(source, masters=self._masters), msg)
            return True
        else:
            return False
    
    def recv_nick(self, user, new_nick):
        '''
            @param user: The user who issued NICK
            @param new_nick: The new NICK
        '''
        if super(ArmageddonBot, self).recv_nick(user, new_nick):            
            self.call_listeners('nick', None, User(user, masters=self._masters), new_nick)      
            return True
        else:
            return False
    
    def recv_mode(self, source, channel, mode, flags, users):
        '''
            @param source: The user who issued the KICK
            @param channel: The channel on which KICK was issued
            @param mode: Flags set or reset (+ or -)
            @param flags: The flags issued
            @param users: The users specified
        '''  
        if super(ArmageddonBot, self).recv_mode(source, channel, mode, flags, users):
            self.call_listeners('mode', channel, User(source, masters=self._masters), (mode, flags, users))
            return True
        else:
            return False
        
    def recv_privmsg(self, user, channel, msg):
        '''
            @param source: The user sending the PRIVMSG
            @param source: The message received
        '''
        if super(ArmageddonBot, self).recv_privmsg(user, channel, msg):            
            if channel == self.current_channel:
                self.call_listeners('msg', channel, User(user, masters=self._masters), msg)
            else:
                self.call_listeners('privmsg', None, User(user, masters=self._masters), msg, only=['cmd'])
            return True
        else:
            return False        
            
        return True
    
    # Overriden stat methods 
    
    def stat_names(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: NAMES is received
        '''        
        return super(ArmageddonBot, self).stat_names(line)
    
    def stat_endnames(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: End of NAMES
            @notice: Used to implement armageddon            
        '''
        Log.write("Usernames %s" % self._names)        
        return super(ArmageddonBot, self).stat_endnames(line)    
    
    def stat_endmotd(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: End of MOTD            
        '''  
        if super(ArmageddonBot, self).stat_endmotd(line):
            self.call_listeners('motd_end', None, None, None)
            return True
        else:
            return False

    def cmd_privmsg(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: End of MOTD   
            @notice: Used to implement commands and actions
        '''
        u = User(line[0].lstrip(':'), masters=self._masters)
        if line[2] == self.params['nick']:                              # If message is a privmsg for bot                    
            if u.role and self.get_status('hear') or u.auth == 0:       # If a valid user and hearing is enabled or user is admin
                Thread(target=self.parse_cmd, args=(u, str.lstrip(' '.join(line[3:]),':'),), name='parse_cmd').start()                        
        elif self.get_status('voice'):            
            if u.role:                                                  # Call extended parser in separate thread                    
                Thread(target=self.parse_msg, args=(u, str.lstrip(' '.join(line[3:]),':'),), name='extended_parse').start()
        
        return super(ArmageddonBot, self).cmd_privmsg(line) 
    
    # Overriden events
    
    def on_bot_terminate(self):
        '''
            @summary: Called when the bot terminates
        '''
        self.save_state()                                     # Save state
        
        if not self.close_requested():                        # Restart was requested
            self._restart_req = True
            self._cv_exit.acquire()
            self._cv_exit.notify_all()
            self._cv_exit.release()
            self._cv_userlist.acquire()
            self._cv_userlist.notify_all()
            self._cv_userlist.release()
            Log.write("Resurrecting...")            
            self._sock = socket.socket();
            Thread(target=self.start, name='start').start()
        else:
            self.call_listeners('exit', None, None, None)
            self._cv_exit.acquire()
            self._cv_exit.notify_all()
            self._cv_exit.release()
            self._cv_userlist.acquire()
            self._cv_userlist.notify_all()
            self._cv_userlist.release()
            Log.write('Bits thou art, to bits thou returnest, was not spoken of....Boom! Owww. *Dead*')            
                            
    def on_bot_mode_set(self):        
        '''
            @summary: Called when a mode is set on the bot.
            @note: Used to trigger commands in queue requiring OP
        '''        
        super(self.__class__, self).on_bot_mode_set()
    
    def on_recv_userhosts(self, nick, userhost):
        '''
            @param nick: The nick
            @param userhost: The nick's userhost
            @summary: Called when the a userhost is received
        '''
        super(self.__class__, self).on_recv_userhosts(nick, userhost)
    
    def on_userlist_complete(self):
        '''            
            @summary: Called when the the userlist has all entries completed
        '''
        if len(self._names):
            self.call_listeners('userlist', None, None, self._names)
    
    # Persistence
    def save_state(self):
        '''
            @summary: Saves the state of the bot and the modules
        '''
        pickler = cPickle.Pickler(open('Qirc.pkl', 'wb'))        
        pickler.dump(self._masters)                
        pickler.dump(self._extmgr.get_state())      # Dump Modules
        pickler.dump(self._cmdmgr.get_state())      # Dump Command Modules        
        
    
    def load_state(self):
        '''
            @summary: Loads the state of the bot and the modules
        '''
        if path.exists('Qirc.pkl'):            
            pickler = cPickle.Unpickler(open('Qirc.pkl', 'rb'))
            try:                
                self._masters = pickler.load()                
                self._extmgr.set_state(pickler.load())      # Mangers will handle pickle errors themselves
                self._cmdmgr.set_state(pickler.load())      # Mangers will handle pickle errors themselves                
            except:
                Log.error('Bad pickle state: ')
    
    # Implementation of parsers  
    def parse_cmd(self, user, cmd):
        '''
            @param role: The group of user
            @param nick: Nick of user
            @param host: Hostname of user
            @param cmd: Command from standard input
            @summary: Parses the command from PM to bot
        '''                        
        if cmd == 'help':
            if user.powers is None:
                self.notice(user.nick, 'Commands are: help, join, part, quit, flag, enforce, module, users, op, say, kick, ban, armageddon')
            else:
                self.notice(user.nick, 'Commands are: %s' % ', '.join(user.powers))
        else:            
            (key, result, success) = self._cmdmgr.parse_line(user, cmd) or (None, None, None)
            if key:            
                if result:
                    self.send_multiline(self.notice, user.nick, result.output)
            else:
                if success is None:
                    if user.powers is None:
                        self.send(cmd)
                    else:
                        self.notice(user.nick, 'You are not authorized to perform this operation. Type /msg %s help to see your list of commands' % self.params['nick'])
        return True
    
    def parse_msg(self, user, msg):
        '''
            @param role: The group of user
            @param nick: Nick of user
            @param host: Hostname of user
            @param msg: Message for bot
            @summary: Specifies additional rules as the general purpose responses
        '''
        Log.write("Parse Message %s" % msg)        
        if msg == '!help':             
            self.send_multiline(self.notice, user.nick, """Enter <command> -h for help on the respective command
 Commands: 
    !help             Shows this help
    !search, !s, !g   Search for a term on various sites
    !calc, !c         Perform some calculation
    !define, !d       Get the meaning, antonyms, etc. for a term
    !quote            Get a quote
    !weather, !w      Get weather and forecasts for a location
    !locate, !l       Locate a user, IP or coordinate
    !url              Perform operation on an url, 
                      Use %N (max 5) to access an earlier url
    !user             Perform operation related to user
    !vote             Start a vote
    !roll             Roll a dice
    !game             Begin a game""")    
    
        else:
            _, result, success = self._extmgr.parse_line(user, msg) or (None, None, None)            
            if not success:
                if result:
                    self.send_multiline(self.notice, user.nick, result.output)                                                    
            elif result:
                self.say(result.output)


# Use the final Bot as QircBot
QircBot = ArmageddonBot
'''    
    @version: 4.0
'''