'''
Created on Jun 7, 2012
@author: Nisheeth Barthwal
'''

from Modules.Manager import DynamicExtensionManager, DynamicCommandManager
from Modules import External, Internal, Commands
        
from QircDatabase import SqliteDb
from QircConfig import QircConfig
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
        
        if len(args) >= 6:            
            self._nick = args[0]
            self._ident = args[1]
            self._host = args[2]
            self._role = args[3]
            self._auth = args[4]
            self._powers = args[5]
            if len(args) == 7:
                self._mgr = args[6]            
        elif len(args) == 1:
            self._nick = None
            self._ident = None
            self._host = None
            self._role = None
            self._auth = None
            self._powers = None
            self._mgr = None
            
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
                        if role == 'chan_mgr':
                            for c,v in masters[role]['channels'].items():
                                if self._host in v:
                                    self._mgr = c
                                    break
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
    
    @property
    def mgr_channel(self):
        return self._mgr


class BaseBot(object):
    '''
        The abstract class BaseBot manages the base working of the bot as well as the interface.
        @version: 3.0
    '''
    
    __metaclass__ = ABCMeta
        
    def __init__(self, config=None, callback=None):
        '''
            @param config    : Configuration for the bot
            @param callback  : A callback function to be called when bot is successfully registered            
        '''
        if config:
            self._config = config
        else:
            self._config = None
            self.load_config()
            
        self._channels = {}
        
        Log.write(self._config)
        
        self._regexes = {}
        
        self._topic = {}                                    # Temporarily hold topics until STATUS 332 is received
        self._sock = socket.socket();
        self._success_callback = callback     
        self._lock = Lock()                                 # mutex _lock [unused]                
        
        self._cv_ping_exit = Condition()
        
        BaseBot.reset_flags(self, build=True)               # Reset bot state
                    
    def load_config(self):
        '''
            @summary: Loads config of the bot
        ''' 
        d = QircConfig()
        if self._config:                                        # If this is a reload
            d['bot']['nick'] = self._config['bot']['nick']      # Preserve bot's nick
        self._config = d
        
    def config(self, *args):
        '''
            @param args: Hierarchy of access leading to the option
            @summary: Returns a config value
        ''' 
        v = None
        d = self._config
        for k in args:
            if d.has_key(k): 
                v = d[k]
                d = v
            else:
                return None
        return v
        
    def channels(self):
        return self._channels.keys()
    
    def channel_flags(self, channel):
        if self._channels.has_key(channel):
            return self._channels[channel]['flags']
        return None
    
    def channel_flag(self, channel, flag):
        if self._channels.has_key(channel):
            return flag in self._channels[channel]['flags']
        else:
            return False
        
    def channel_members(self, channel):
        if self._channels.has_key(channel):
            return self._channels[channel]['members']
        return None
    
    def channel_member(self, channel, nick):
        if self._channels.has_key(channel) and self._channels[channel]['members'].has_key(nick):
            return self._channels[channel]['members'][nick]
        return None
    
    def get_user_channel(self, nick, index=0):
        idx = max(index, 0)
        for k,v in self._channels.items():
            for u in v['members'].keys():                
                if nick == u:
                    if idx == 0:
                        return k
                    else:
                        idx = idx - 1
        return None
        
    def channel_topic(self, channel):
        if self._channels.has_key(channel) and self._channels[channel].has_key('topic'):
            return self._channels[channel]['topic']
        return None
        
    def reset_flags(self, build):
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
        
    def bot_connected(self):
        '''
            @summary: Called when the bot has connected to the server
        '''
        if self._success_callback:
            Thread(target=self._success_callback, args=(self,), name='callback').start()        # Call callback function
        
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
            self._sock.connect((self.config('server', 'url'), self.config('server', 'port')))
            self._sock.setblocking(0)            
            self._retry_timeout = 15
            return True
        except socket.error, e:
            Log.write('Failed to connect %s Reconnecting in %d seconds' % (e, self._retry_timeout))
            #time.sleep(self._retry_timeout)
            if self._retry_timeout < 180:
                self._retry_timeout *= 1.5                      # Increase retry time after every failure
            else:
                self._retry_timeout = 180                       # Limit retry time to 3 minutes
    
    def register(self):
        '''
            @summary: Registers the bot on IRC
        '''
        self.send("NICK %s" % self.config('bot', 'nick'))
        self.send("USER %s %s bla :%s" % (self.config('bot', 'ident'), self.config('server', 'url'), self.config('bot', 'realname')))
    
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
        Log.write('Starting read loop') 
        try:            
            self._read_buffer = ''
            run_read = True
            chunk = '+'                             # Initially chunk not empty
            while run_read and self._alive and not self.close_requested() and not self.restart_requested():
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
        Log.write('Read loop terminated') 
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
            
        self.on_connected()
        self.begin_read()
        self.register()                
    
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
    
    def __init__(self, config=None, callback=None):
        '''
            @param config    : Configuration for the bot
            @param callback  : A callback function to be called when bot is successfully registered
        '''
        super(ActiveBot, self).__init__(config, callback)
        ActiveBot.reset_flags(self, bubble=False, build=True)                 # Initialize flags but do not bubble up, since already set by BaseBot.__init__()
         
        self._op_actions = {}                              # Named ThreadQueues for OP functions per channel        
        self._multisend_lock = Lock()                      # Thread lock for avoiding floodkicks on send_multiline()
        self._cv_userlist = Condition()                    # Condition Variable for requesting userlist
        self._cv_autojoin = Condition()                    # Condition Variable for requesting userlist
    
    def bot_connected(self):
        '''
            @summary: Called when the bot has connected to the server
        '''
        super(ActiveBot, self).bot_connected()
        for c in self.config('startup', 'channels'):            
            self.join(c)
        msg = self.config('startup', 'notice-msg')
        for n in self.config('startup', 'notice-to'):            
            self.notice(n, msg)
            
    def notify_all_threads(self):
        '''
            @summary: Notifies all waiting threads
        '''
        Log.write('Notifying pinger CV')
        self._cv_ping_exit.acquire()
        self._cv_ping_exit.notify_all()
        self._cv_ping_exit.release()        
        Log.write('Notifying userlist CV')
        self._cv_userlist.acquire()
        self._cv_userlist.notify_all()
        self._cv_userlist.release()
        Log.write('Notifying autojoin CV')
        self._cv_autojoin.acquire()
        self._cv_autojoin.notify_all()
        self._cv_autojoin.release()
        
    def reset_flags(self, bubble, build):
        '''
            @param bubble: Whether to reset the flags in the base class
            @param build: If true, then status_flags are initialized
            @summary: Resets the state flags of the bot 
        '''
        self._alive = True
        self._joined = False
        self._pong_recv = True
        self._ghost = False
        self._has_quit = False
        self._restart_req = False
        #self._members = {}
        self._retry_channels = {}
        if bubble:
            BaseBot.reset_flags(self, build)
        
    def cleanup(self):
        '''
            @summary: Performs any cleanup activity while qutting the bot
        '''        
        BaseBot.cleanup(self)    
    
    def request_memberlist(self, channel=None):
        '''
            @summary: Activates a request for raising `userlist` event
        '''
        self._cv_userlist.acquire()
        if channel:
            self._request_memberlist = [channel]
        else:
            self._request_memberlist = self.channels()
        self._cv_userlist.notify()
        self._cv_userlist.release()
    
    def autojoin_retry(self):
        '''
            @summary: Retries joining channels
        '''               
        while self._alive and not self.close_requested() and not self.restart_requested():
            try:    
                self._cv_autojoin.acquire()
                self._cv_autojoin.wait(10)        # Wait every 10 seconds
                self._cv_autojoin.release()
                if len(self._retry_channels) and self._alive and not self.close_requested() and not self.restart_requested():                    
                    for k in self._retry_channels.keys():
                        self._retry_channels[k] = (self._retry_channels[k][0], self._retry_channels[k][1] + 10)
                        if self._retry_channels[k][0] <= self._retry_channels[k][1]:                     # If waited more than threshold
                            self._retry_channels[k] = (min(self._retry_channels[k][0] * 1.25, 180), 0)  # Exponential backoff, Try joining                            
                            self.join(k)                                                    
                                         
            except Exception, e:
                Log.error(e)
        Log.write('Terminated: autojoin_retry()')
                
    def memberlist_buildup(self):
        '''
            @summary: Builds a {nick : username} dict for all the members in every channel at periodic intervals
        '''                        
        try:

            self._cv_userlist.acquire()
            self._cv_userlist.wait()        # Wait for signal to proceed
            self._cv_userlist.release()
            if self._alive and not self.close_requested() and not self.restart_requested():
                self._cv_userlist.acquire()
                self._cv_userlist.wait(10)        # Delay 10 seconds to receive NAMES
                self._cv_userlist.release()                  
        except:
            pass
        
        self._request_memberlist = []
        old_channels_requested = []
        while self._alive and not self.close_requested() and not self.restart_requested():                    
            try:                                                
                channels_requested = []
                for c,d  in self._channels.items():                                  # For every connected channel
                    l = []                                                      # Check if any nick doesn't have the username entry
                    for k,v in d['members'].items():
                        if v is None:
                            l.append(k)
                    if len(l):                                                  # Request hostnames of empty nicks
                        channels_requested.append(c)
                        for n in chunk(l, 5):
                            self.userhosts(' '.join(n))
                        Log.write('Requesting Userlist: %s' % l, 'D')
                    #else:                    
                    #    Log.write('Complete Userlist: %s' % self._members.keys(), 'D')
                
                self._cv_userlist.acquire()
                if len(channels_requested):
                    olen = len(old_channels_requested)
                    if olen and olen != len(channels_requested):
                        for c in set(old_channels_requested) - set(channels_requested):
                            self.on_userlist_complete(c)
                    if len(self._request_memberlist):
                        self._cv_userlist.wait(5)                           # Recheck after 5 seconds if list is requested
                    else:
                        self._cv_userlist.wait(10)                          # Recheck after 30 seconds otherwise
                elif len(self._request_memberlist):                                # If list was requested and not pending, then trigger event
                    for c in self._request_memberlist:
                        self.on_userlist_complete(c)
                    self._request_memberlist = []                                        
                    self._cv_userlist.wait(60)                              # Sleep for 60 seconds
                else:                    
                    self._cv_userlist.wait(60)                              # Sleep for 60 seconds
                self._cv_userlist.release()                    
            except Exception, e:
                Log.error(e)  
            old_channels_requested = channels_requested
        Log.write('Terminated: memberlist_buildup()')
                                        
            
    def server_ping(self):        
        '''
            @summary: Pings the server every 90 seconds to keep the connection alive
        '''
        while self._pong_recv and not self.close_requested() and not self.restart_requested():           # If PONG was received for the previous PING, if not the connection is probably dead            
            self._pong_recv = False
            try:                        
                self._cv_ping_exit.acquire()
                self._cv_ping_exit.wait(60)                                  # PING every 60 seconds
                self._cv_ping_exit.release()                
                        
                if not self.close_requested() and not self.restart_requested():
                    self.ping()                                         # Send PING                
                    self._cv_ping_exit.acquire()
                    self._cv_ping_exit.wait(30)                              # Wait 30 seconds for a PONG
                    self._cv_ping_exit.release()                 
            except:
                pass
        
        self._alive = False
        if not self.close_requested() and not self.restart_requested():
            self._cv_ping_exit.acquire()
            self._cv_ping_exit.notify_all()
            self._cv_ping_exit.release()
        '''
        try:
            self.ping()                                                     # Precautionary PING to unblock the socket.recv()
        except:
            pass
        '''
        Log.write('Server failed to respond to PONG')
            
    def queue_op_add(self, channel, target, args=(), kwargs={}):
        '''
            @param channel: Channel name to identify a queue
            @param target: The function
            @param args: Arguments to function
            @param kwargs: Keyworded arguments to function
            @attention: Function name at [0] and arguments after that
            @summary: Adds a item to the queue for processing once the bot is OPed
        '''
        self._lock.acquire()
        if not self._op_actions.has_key(channel):
            self._op_actions[channel] = ThreadQueue()
        self._op_actions[channel].put(target, args, kwargs)
        self._lock.release()
    
    def queue_op_process(self, channel):
        '''
            @param channel: Channel name to identify a queue
            @summary: Processes the tasks once the bot is OPed
        '''
        self._lock.acquire()
        if self._op_actions.has_key(channel) and self._op_actions[channel].length:
            self._op_actions[channel].process()                              # Process
            self._op_actions[channel].join()                                 # Block until complete
            self.deop(channel, self.config('bot', 'nick'))
            self.set_flags(channel, 'o', value=False)                        # Precautionary measure
        self._lock.release()
            
    def get_flag(self, channel, key=None):
        '''
            @param key: Key of the flag, None if all flags are required
            @return: Returns flag status else all flags            
        '''
        if key is None:
            return self.channel_flags(channel).items()
        else:
            return self.channel_flag(channel, key)        
    
    def set_flags(self, channel, key=None, value=None, flag_dict=False):
        '''
            @param key: Key to flags
            @param value: The new value to set, if required 
            @param flag_dict: If true, then the entire dict is set/returned
            @return: Returns True if the status is set, else False
        '''
        if flag_dict:
            if value is None:
                return self.channel_flags(channel)
            else:        
                self._channels[channel]['flags'] = value
        else:
            if key is None:
                return self.channel_flags(channel).items()
            else:
                if value is not None:
                    if value:
                        if key not in self._channels[channel]['flags']:
                            self._channels[channel]['flags'].append(key)
                    else:
                        if key in self._channels[channel]['flags']:
                            self._channels[channel]['flags'].remove(key)
                    return value                
                else:
                    return self.channel_flag(channel, key)
        
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
        self.send("PING %s" % self.config('server', 'url'))
        
    def join(self, channel, key=''):
        '''
            @param channel: The channel to join. Example #channel
            @summary: Sends a JOIN command to join the channel and updates the current channel
        '''                
        self.send('JOIN %s %s' % (channel, key))
        
    def part(self, channel, msg=''):
        '''
            @param msg: PART message
            @summary: Parts the bot from a channel
        '''
        self.send("PART %s :%s" % (channel, msg))        
        
    def identify(self):
        '''
            @summary: Sends a message to identify bot's NICK 
        '''
        if self.config('bot', 'password'):
            self.send("PRIVMSG nickserv :identify %s" % self.config('bot', 'password'))
        
    def ghost(self, nick):
        '''
            @param nick: NICK to ghost
            @summary: Sends a message to NickServ to ghost a NICK
        '''
        if self.config('bot', 'password'):
            Log.write("Ghosting nick...")
            self.send("PRIVMSG nickserv :ghost %s %s" % (nick, self.config('bot', 'password')))        
    
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
    
    def say(self, channel, msg):     
        '''
            @param msg: Message to say
            @summary: Say something in the current channel
        '''   
        self.send('PRIVMSG %s :%s' % (channel, msg))
        
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
            
    def kick(self, channel, nick, msg, auto_op=True):        
        '''
            @param channel: Channel name
            @param nick: User nick
            @param msg: KICK reason
            @param auto_op: If set to true ensures that the bot is +o'd first
            @summary: Kicks a user from the channel
            @attention: Requires OP mode
        '''
        if self.get_status('kick') and nick != self.config('bot', 'nick'):     # Avoid kicking self
            if self.channel_flag(channel, 'o'):
                self.send('KICK %s %s %s' % (channel, nick, ' :'+msg if msg else ''))
            elif auto_op:
                self.queue_op_add(channel, target=self.kick, args=(channel, nick, msg, False,))
                self.op(channel, self.config('bot', 'nick'))
    
    def ban(self, channel, host, auto_op=True):
        '''
            @param channel: Channel name
            @param host: User's hostmask
            @param auto_op: If set to true ensures that the bot is +o'd first
            @summary: Bans a user from the channel
            @attention: Requires OP mode
        '''
        if self.get_status('ban') and host.lstrip("*!*@") != self.channel_member(channel, self.config('bot', 'nick')).host:
            if self.channel_flag(channel, 'o'):
                self.send('MODE %s +b %s' % (channel, host,))
            elif auto_op:
                self.queue_op_add(channel, target=self.ban, args=(channel, host, False,))    
                self.op(channel, self.config('bot', 'nick'))        
    
    def kickban(self, channel, nick, host, msg, auto_op=True):        
        '''
            @param channel: Channel name
            @param nick: User nick
            @param msg: KICK reason
            @param auto_op: If set to true ensures that the bot is +o'd first
            @summary: Kicks a user from the channel
            @attention: Requires OP mode
        '''        
        if self.get_status('kick') and self.get_status('ban') and nick != self.config('bot', 'nick'):     # Avoid kicking self
            if self.channel_flag(channel, 'o'):
                self.ban(channel, host)
                self.kick(channel, nick, msg)                
            elif auto_op:
                self.queue_op_add(channel, target=self.kickban, args=(channel, nick, host, msg, False,))
                self.op(channel, self.config('bot', 'nick'))
                
    def unban(self, channel, host, auto_op=True):    
        '''
            @param channel: Channel name
            @param host: User's hostmask
            @param auto_op: If set to true ensures that the bot is +o'd first
            @summary: Unbans a user from the channel
            @attention: Requires OP mode
        ''' 
        if self.channel_flag(channel, 'o'):
            self.send('MODE %s -b %s' % (channel, host))
        elif auto_op:
            self.queue_op_add(channel, target=self.unban, args=(channel, host, False,))    
            self.op(channel, self.config('bot', 'nick'))
    
    def members(self, channel): 
        '''
            @summary: Send a NAME command to get the list of usernames in the current channel
        '''       
        self.send('NAMES %s' % channel)        
    
    def userhosts(self, members):
        '''
            @param members: Space separated string of upto 5 nicks
            @summary: Send a USERHOST command to get the list of upto 5 userhosts in the current channel
        '''       
        self.send("USERHOST %s" % members)
        
    def action(self, channel, msg):
        '''
            @param msg: Message to display
            @summary: Send an ACTION message
        '''
        self.send("PRIVMSG %s :\x01ACTION %s\x01" % (channel, msg))
    
    def op(self, channel, nick):
        '''
            @param channel: Channel name
            @param nick: Nick of the user to op            
            @summary: OPs the user in a given channel
        '''
        self.send("PRIVMSG ChanServ :op %s %s" % (channel, nick))
        
    def deop(self, channel, nick):
        '''
            @param channel: Channel name
            @param nick: Nick of the user to deop            
            @summary: DEOPs the user in a given channel
        '''
        self.send("PRIVMSG ChanServ :deop %s %s" % (channel, nick))                    
    
    def parse_recv(self, recv):
        '''
            @param recv: Messages from IRC
            @summary: Parses the messages coming from the IRC to take suitable actions
        '''
        loop = True
        for line in recv:
            line=line.rstrip()        # Strip '\r' characters if present
            if len(line):
                Log.write(line)    # Print line
                line=str.split(line)         # Split elements            
                    
                # Important Messages
                if(line[0] == "PING"):                          # PING from server
                    loop = loop and self.cmd_ping(line) 
                elif(line[1] == "PONG"):                        # PONG from server
                    loop = loop and self.cmd_pong(line)
                elif(line[1] == "QUIT"):                        # QUIT
                    loop = loop and self.cmd_quit(line)
                elif(line[1] == "PART"):                        # PART
                    loop = loop and self.cmd_part(line)
                elif(line[1] == "JOIN"):                        # JOIN
                    loop = loop and self.cmd_join(line)
                elif(line[1] == "KICK"):                        # KICK
                    loop = loop and self.cmd_kick(line)
                elif(line[1] == "NOTICE"):                      # NOTICE
                    loop = loop and self.cmd_notice(line)
                elif(line[1] == "NICK"):                        # NICK
                    loop = loop and self.cmd_nick(line)     
                elif(line[1] == "MODE"):                        # MODE
                    loop = loop and self.cmd_mode(line) 
                elif(line[1] == "TOPIC"):                        # TOPIC
                    loop = loop and self.cmd_topic(line) 
                    
                # Control Messages
                elif line[1] == "433":                          # NICK already in use                
                    loop = loop and self.stat_nickuse(line)
                elif line[1] == "375":                          # Start of /MOTD command
                    loop = loop and self.stat_startmotd(line)
                elif line[1] == "371" or line[1] == "372":      # MOTD                
                    loop = loop and self.stat_motd(line)
                elif line[1] == "376":                          # End of /MOTD command
                    loop = loop and self.stat_endmotd(line)
                elif line[1] == "331":                          # NO TOPIC : Response
                    loop = loop and self.stat_notopic(line)
                elif line[1] == "332":                          # TOPIC : Response
                    loop = loop and self.stat_topic_text(line)
                elif line[1] == "333":                          # TOPIC_BY
                    loop = loop and self.stat_topic_by(line)
                elif line[1] == "353":                          # NAMES
                    loop = loop and self.stat_names(line)
                elif line[1] == "366":                          # End of /NAMES list
                    loop = loop and self.stat_endnames(line)              
                elif line[1] == "302":                          # USERHOST
                    loop = loop and self.stat_userhost(line)            
                elif line[1] == "462":                          # Already registered
                    loop = loop and self.stat_already_registered(line)
                elif line[1] in ["471", "473", "474", "475"]:   # Full, Invite, Banned, Key-Req
                    loop = loop and self.err_nojoin(line) 
                # Basic Messages
                elif line[1] == "PRIVMSG": 
                    loop = loop and self.cmd_privmsg(line)
                                                           
        return loop
    
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
    
    def cmd_topic(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: TOPIC was received
        '''                
        return self.recv_topic(line[2], line[0].lstrip(':'), time.time(), ' '.join(line[3:]).lstrip(':')) 
    
    def stat_topic_text(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: TOPIC response
        '''
        self._topic[line[3]] = ' '.join(line[4:]).lstrip(':')
        return True
        #self._channels[line[3]]['topic'] = ' '.join(line[4:]).lstrip(':')
        #return self.recv_topic(line[0].lstrip(':'), line[2], ' '.join(line[3:]).lstrip(':'))
    
    def stat_topic_by(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: TOPIC was set by
        '''                
        if self._topic.has_key(line[3]):
            t = self._topic[line[3]]
            self._topic.pop(line[3])
        return self.recv_topic(line[3], line[4], line[5], t)
        
    def stat_notopic(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: No TOPIC is set
        '''
        return self.recv_notopic(line[3])
    
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
            self._config['bot']['nick'] = self.config('bot', 'attempt-nick') + str(random.randrange(1,65535)) 
            Log.write('Retrying with nick %s' % self.config('bot', 'nick'))
            self._ghost = self.config('bot', 'password') is not None   # Ghost other user/bot if password is specified
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
            self.ghost(self.config('bot', 'attempt-nick'))                    
            self._ghost = False
        else:
            self.identify()                         # Normal join, just identify
            self.bot_connected()            
        
        self.reset_flags(bubble=True, build=False)               # Give bot a fresh start
                            
        return True
    
    def stat_names(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: NAMES is received
        '''
        for x in line[5:]:
            self._channels[line[4]]['members'][x.strip(':@+')] = None      # Add members to current list            
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
                for k in self.channels():
                    if self._channels[k]['members'].has_key(nick):
                        self._channels[k]['members'][nick] = User(nick + '!' + m.group(2))
                self.on_recv_userhosts(nick, m.group(2))
        return True
        
    def stat_already_registered(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: ERR_ALREADYREGISTERED is received          
        '''
        self.identify()                         # Normal join, just identify
        return True
    
    def err_nojoin(self, line):
        '''
            @param line: The text received broken into tokens
            @summary: Content of ERR_CHANNELISFULL, ERR_INVITEONLYCHAN, ERR_BANNEDFROMCHAN and ERR_BADCHANNELKEY
        '''
        self.on_bot_nojoin(line[1], line[3], ' '.join(line[4:]).lstrip(':'))
        return True
    
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
        for k, v in self._channels.items():
            if u.nick in v['members'].keys():
                self._channels[k]['members'].pop(u.nick)
                #self._members[k].pop(u.nick)
                self.on_userlist_update(k)
        if u.nick == self.config('bot', 'nick'):                    
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
        if self.channel_member(channel, u.nick):
            self._channels[channel]['members'].pop(u.nick)
        self.on_userlist_update(channel)
        if u.nick == self.config('bot', 'nick'):
            self.on_bot_part(channel)
        return True
    
    def recv_join(self, user, channel):
        '''
            @param user: The user that joined
            @param channel: The channel that was joined to
        '''
        if not self._channels.has_key(channel): 
            self._channels[channel] = {
                                        'flags': [],
                                        'members': {}
                                       }
        if self._retry_channels.has_key(channel):
            self._retry_channels.pop(channel)
        u = User(user, simple=True)        
        self._channels[channel]['members'][u.nick] = u
        self.on_userlist_update(channel)
        if u.nick == self.config('bot', 'nick'):
            #self._members[channel] = {}         # Remove self name from userlist
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
        if self.channel_member(channel, user):
            self._channels[channel]['members'].pop(user)
        self.on_userlist_update(channel)
        if user == self.config('bot', 'nick'):                         # If bot is kicked
            self._retry_channels[channel] = (10, 0)
            self._cv_autojoin.acquire()
            self._cv_autojoin.notify_all()
            self._cv_autojoin.release()
            #self.join(channel)
        return True
    
    def recv_notice(self, source, broadcast, msg):
        '''
            @param source: The source of the NOTICE
            @param broadcast: True if the notice is a broadcasted notice 
            @param msg: The message received
        '''
        if msg.find(' has been ghosted') != -1:                 # Duplicate NICK has been ghosted
            self.nick(self.config('bot', 'attempt-nick'))                           # Claim original NICK
            self.identify()                                     # Identify
            self.bot_connected()
            
        return True
    
    def recv_nick(self, nick, new_nick):
        '''
            @param nick: The nick who issued NICK
            @param new_nick: The new NICK
        '''                
        u = User(nick, simple=True)
        for k, v in self._channels.items():
            if u.nick in v['members'].keys():
                self._channels[k]['members'].pop(u.nick)
                self._channels[k]['members'][new_nick]= u
                #self._members[k].pop(u.nick)
                #self._members[k][new_nick] = u
                self.on_userlist_update(k)
                                       
        if u.nick == self.config('bot', 'nick'):
            self._config['bot']['nick'] = new_nick
            self.on_bot_nick_change(self.config('bot', 'nick'))
            self.call_listeners('botnick', None, u, self.config('bot', 'nick'))            
        return True
    
    def recv_mode(self, source, channel, mode, flags, users):
        '''
            @param source: The user who issued the KICK
            @param channel: The channel on which KICK was issued
            @param mode: Flags set or reset (+ or -)
            @param flags: The flags issued
            @param users: The users specified
        '''        
        if users and self.config('bot', 'nick') in users:    # Mode is set on an user and not on channel (hence the 4th index)                  
            for f in flags:
                if f not in self._channels[channel]['flags'] and mode == '+':
                    self._channels[channel]['flags'].append(f)
                elif f in self._channels[channel]['flags'] and mode == '-':
                    self._channels[channel]['flags'].remove(f)
            
            if mode == '+':
                self.on_bot_mode_set(channel)
            else:
                self.on_bot_mode_reset(channel)
        return True
    
    def recv_topic(self, channel, user, timestamp, topic):
        '''
            @param user: The user changing the TOPIC
            @param channel: The channel name
            @param topic: The new topic
        '''        
        self._channels[channel]['topic'] = {
                                                'text'  : topic,
                                                'user'    : user,
                                                'time'  : timestamp
                                            }    
        return True
    
    def recv_notopic(self, channel):
        '''
            @param user: The user changing the TOPIC
            @param channel: The channel name
            @param topic: The new topic
        '''
        self._channels[channel]['topic'] = {
                                                'text'  : '',
                                                'by'    : None,
                                                'time'  : 0
                                            }
        return True
    
    def recv_privmsg(self, user, channel, msg):
        '''
            @param user: The user sending the PRIVMSG
            @param channel: The channel name
            @param msg: The message received
        '''            
        return True
            
    def on_connected(self):
        '''
            @summary: Called when the bot is connected
        '''        
        self.reset_flags(bubble=True, build=False)
        Log.write('Starting worker threads')
        Thread(target=self.server_ping, name='ActiveBot.server_ping').start()               # Start pinger thread
        Thread(target=self.memberlist_buildup, name='ActiveBot.memberlist_buildup').start()     # Start userlist monitoring thread
        Thread(target=self.autojoin_retry, name='ActiveBot.autojoin_retry').start()         # Start autojoin retry thread
    
    def on_bot_join(self, channel):
        '''
            @param channel: The channel name
            @summary: Called when the bot joins a channel
        '''          
        pass
    
    def on_bot_part(self, channel):
        '''
            @param channel: The channel name
            @summary: Called when the bot parts the channel
        '''        
        if self._channels.has_key(channel): 
            self._channels.pop(channel)     # Reset  channel from state, if parted
    
    def on_bot_mode_set(self, channel):
        '''
            @summary: Called when a mode is set on the bot
        '''
        if self.channel_flag(channel, 'o'):
            Thread(target=self.queue_op_process, args=(channel,), name='QircBot.queue_op_process').start() 
        pass
    
    def on_bot_mode_reset(self, channel):
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
    
    def on_bot_nojoin(self, code, channel, reason):
        '''            
            @param code: The error code
            @param channel: The channel
            @param reason: The reason for error
            @summary: Called when the the userlist is changed
        '''
        if channel not in self._retry_channels: 
            self._retry_channels[channel] = (10, 0)     # Next try, Duration left
    
    def on_userlist_complete(self, channel):
        '''            
            @param channel: The channel name
            @summary: Called when the the userlist has all entries completed
        '''
        pass
    
    def on_userlist_update(self, channel):
        '''            
            @summary: Called when the the userlist is changed
        '''
        Log.write('Updated Userlist: %s : %s' % (channel, self.channel_members(channel).keys()), 'D')
        pass
    
    def dispatch_userlist_update(self, nick):
        '''
            @summary: Triggers userlist update for all channels the user is part of 
        '''
        for k, v in self._channels.items():
            if nick in v['members'].keys():
                self.on_userlist_update(k)
    
class ArmageddonBot(ActiveBot):
    '''
        @summary: Incorporates complex functionality into the bot
        @version: 5.0
    '''    
    
    def __init__(self, config=None, callback=None):
        '''
            @param config    : Configuration for the bot
            @param callback  : A callback function to be called when bot is successfully registered
        '''
        super(QircBot, self).__init__(config, callback)        
        
        self.reset_flags(bubble=False, build=True)
                
        self._masters = {
                            'admin' :   {
                                            'auth'    : 0,
                                            'members' : self.config('bot', 'owner'),
                                            'powers'  : None
                                        },
                            'mod'   :   {   
                                            'auth'    : 50,                      
                                            'members' : [],
                                            'powers'  : ['help', 'flags', 'op', 'kick', 'enforce', 'ban', 'module', 'users', 'armageddon']
                                        },
                            'mgr'   :   {                
                                            'auth'    : 150,
                                            'members' : [],
                                            'powers'  : ['help', 'flags', 'op', 'kick', 'enforce', 'ban', 'unban']
                                        },
                            'chan_mgr'   :   {                
                                            'auth'    : 254,
                                            'channels' : {
                                                            '#nbaztec': ['unaffiliated/nbaztec']
                                                          },
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
            if k == 'chan_mgr':
                l = []
                for m in v['channels'].values():                    
                    l.extend(m)
                l = list(set(l))
                self._special_users.append('(?P<%s>%s)' % (k, '|'.join(l)))
            elif k != 'others':                           # Ensure others is last
                self._special_users.append('(?P<%s>%s)' % (k, '|'.join(v['members'])))
        self._special_users.append('(?P<%s>%s)' % ('others', '|'.join(self._masters['others']['members'])))
        self._regexes['special'] = re.compile(r'^([^!]+)!(~*[^@]+)@(%s)$' % '|'.join(self._special_users))         # Regex for matching hostmask of users
        
        User.set_special_regex(self._regexes['special'])
            
    def load_commands(self):
        '''            
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
            @param ext_type: Type of extension to load 0:Both, 1:Internal, 2:External 
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
                    instance = obj(self)
                    if instance.key == key:
                        Log.write('Importing : %s' % name)
                        self._extmgr.add(instance, False)
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
        try:
            if mgr_type == 0:
                return self._extmgr.module(key)
            elif mgr_type == 1:
                return self._cmdmgr.module(key)
        except:
            return None
        
    def get_modules(self, mgr_type=0):
        '''            
            @param mgr_type: The manager to select - extension/command (0/1)
            @return: Iterator on modules
        '''
        if mgr_type == 0:
            return self._extmgr.modules()
        elif mgr_type == 1:
            return  self._cmdmgr.modules()
        
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
        for v in self._channels.values():
            if nick in v['members'].keys():
                return v[nick]        
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
        
    def user_list(self, channel=None, sort=False):
        '''
            @summary: Returns the list of masters as a dict
        '''
        d = []
        sdict = self._masters.items()
        if sort:
            sdict = sorted(sdict, key=lambda x: x[1]['auth'])
        for k, v in sdict:
            if k == 'chan_mgr':
                l = []
                for c,m in v['channels'].items():
                    l.append('%s = %s' % (c, ';'.join(m)))
                d.append((k, l))
            elif k != "others":
                d.append((k, v['members']))
        return d
    
    def power_list(self, sort=False):
        '''
            @summary: Returns the list of groups and their powers as a dict
        '''
        d = []
        sdict = self._masters.items()
        if sort:
            sdict = sorted(sdict, key=lambda x: x[1]['auth'])
        for k, v in sdict:
            if k != "others":
                d.append((k, v['powers']))
        return d
    
    def role_list(self, sort=False):
        '''
            @summary: Returns the list of groups and their auths as a dict
        '''
        d = []
        sdict = self._masters.items()
        if sort:
            sdict = sorted(sdict, key=lambda x: x[1]['auth'])
        for k, v in sdict:
            if k != "others":
                d.append((k, v['auth']))
        return d
            
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
                      
    def user_add(self, role, hostname, channel=None):
        '''
            @param role: The group of user
            @param hostname: The hostname of user
            @summary: Adds the hostname to a specified group of masters
        '''
        if self._masters.has_key(role):
            if role == 'chan_mgr':
                if channel:
                    if not self._masters[role]['channels'].has_key(channel):
                        self._masters[role]['channels'][channel] = []
                    if hostname not in self._masters[role]['channels'][channel]:
                        self._masters[role]['channels'][channel].append(hostname)
                        self.regex_prepare_users()
                        return True
            elif hostname not in self._masters[role]['members']:
                self._masters[role]['members'].append(hostname)
                self.regex_prepare_users()
                return True        
    
    def user_remove(self, role, hostname, channel=None):
        '''
            @param role: The group of user
            @param hostname: The hostname of user
            @summary: Removes the hostname from a specified group of masters
        '''
        if self._masters.has_key(role):
            if role == 'chan_mgr':
                if channel and self._masters[role]['channels'].has_key(channel) and hostname in self._masters[role]['channels'][channel]:
                    self._masters[role]['channels'][channel].remove(hostname)
                    self.regex_prepare_users()
                    if len(self._masters[role]['channels'][channel]) == 0:
                        self._masters[role]['channels'].pop(channel)
                    return True
            elif hostname in self._masters[role]['members']:
                if role == 'admin' and len(self._masters[role]['members']) == 1:
                    return None
                self._masters[role]['members'].remove(hostname)
                self.regex_prepare_users()
                return True        
            
    def user_auth(self, hostmask=None, role=None):
        '''
            @param hostmask: The hostmask's hostmask
            @param role: The group name
            @summary: Returns the authority level of the hostmask or group
        '''
        if hostmask:
            for v in self._masters.values():
                if v.has_key('channels'):
                    for c in v['channels'].values():
                        if hostmask in c:
                            return v['auth']
                elif hostmask in v['members']:
                    return v['auth']
        elif role:
            if self._masters.has_key(role):
                return self._masters[role]['auth']     
            
    def add_retry_channel(self, channel):
        '''
            @param channel: Channel name
        '''
        self._retry_channels[channel] = (10, 0)
        
    def remove_retry_channel(self, channel):
        '''
            @param channel: Channel name
        '''
        if self._retry_channels.has_key(channel):
            self._retry_channels.pop(channel)
            return True
        else:
            return False;
        
    def retry_channels(self, channels=None):
        '''
            @param channels: List of channels to set
            @returns: List of channels
        '''
        if channels:
            for c in channels:
                self.add_retry_channel(c)
        else:
            return self._retry_channels.keys()
        
    # Overriden recv methods
    def reset_flags(self, bubble, build):
        '''
            @param bubble: Whether to reset the flags in the base class
            @param build: If true, then status_flags are initialized
            @summary: Resets the state flags of the bot 
        '''        
        if bubble:
            super(ArmageddonBot, self).reset_flags(bubble, build)
                       
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
        self.members(channel)
        self.say(channel, 'All systems go!')
        
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
        if u.nick == self.config('bot', 'nick'):
            self.call_listeners('botquit', None, u, reason)
        else:
            for k, v in self._channels.items():
                if u.nick in v['members'].keys():
                    self.call_listeners('quit', k, u, reason)            
        return super(ArmageddonBot, self).recv_quit(user, reason)
            
    def recv_part(self, user, channel, reason):
        '''
            @param user: The user that parted
            @param channel: The channel that was parted from
        '''        
        u = User(user, masters=self._masters)
        if u.nick != self.config('bot', 'nick'):
            self.call_listeners('part', channel, u, reason)
        else:
            self.call_listeners('botpart', channel, u, reason)
        return super(ArmageddonBot, self).recv_part(user, channel, reason)
    
    def recv_kick(self, source, channel, user, reason):
        '''
            @param source: The user who issued the KICK
            @param channel: The channel on which KICK was issued
            @param user: The user who got kicked
            @param reason: The reason for kicking 
        '''
        if self.channel_member(channel, user):
            self.call_listeners('kick', channel, self.channel_member(channel, user), (User(source, masters=self._masters), reason))            
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
    
    def recv_nick(self, nick, new_nick):
        '''
            @param nick: The nick who issued NICK
            @param new_nick: The new NICK
        '''
        if super(ArmageddonBot, self).recv_nick(nick, new_nick):
            for k, v in self._channels.items():
                if nick in v['members'].keys():
                    self.call_listeners('nick', k, User(nick, masters=self._masters), new_nick)      
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
        
    def recv_topic(self, channel, user, timestamp, topic):
        '''
            @param user: The user changing the TOPIC
            @param channel: The channel name
            @param topic: The new topic
        '''            
        if super(ArmageddonBot, self).recv_topic(channel, user, timestamp, topic):
            self.call_listeners('topic', channel, User(user, masters=self._masters), (timestamp, topic))
            return True
        else:
            return False
    
    def recv_privmsg(self, user, channel, msg):
        '''
            @param user: The user sending the PRIVMSG
            @param channel: The channel name
            @param msg: The message received
        '''        
        if super(ArmageddonBot, self).recv_privmsg(user, channel, msg):            
            if channel.startswith('#'):
                m = re.match(r'\x01ACTION (.*)\x01', msg)
                if m:                                        
                    self.call_listeners('action', channel, User(user, masters=self._masters), m.group(1))
                else:
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
        Log.write("Usernames %s" % self._channels)        
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
        if line[2] == self.config('bot', 'nick'):                              # If message is a privmsg for bot                    
            if u.role and self.get_status('hear') or u.auth == 0:       # If a valid user and hearing is enabled or user is admin
                Thread(target=self.parse_cmd, args=(u, str.lstrip(' '.join(line[3:]),':'),), name='parse_cmd').start()                        
        elif self.get_status('voice'):            
            if u.role:                                                  # Call extended parser in separate thread                    
                Thread(target=self.parse_msg, args=(line[2], u, str.lstrip(' '.join(line[3:]),':'),), name='extended_parse').start()
        
        return super(ArmageddonBot, self).cmd_privmsg(line) 
    
    # Overriden events
    
    def on_bot_terminate(self):
        '''
            @summary: Called when the bot terminates
        '''
        Log.write("Bot terminated")
        self.save_state()                                     # Save state
        
        if not self.close_requested():                        # Restart was requested
            Log.write('Attempting to restart')
            self._restart_req = True
            self._sock.close()
            Log.write('Notifying all threads')
            self.notify_all_threads()
            Log.write('Waiting for 5 seconds')
            time.sleep(5)                                     # Wait 5 seconds
            Log.write("Resurrecting...")            
            self._sock = socket.socket();
            Thread(target=self.start, name='start').start()
        else:
            self.call_listeners('exit', None, None, None)
            self.notify_all_threads()
            Log.write('Bits thou art, to bits thou returnest, was not spoken of....Boom! Owww. *Dead*')            
                            
    def on_bot_mode_set(self, channel):        
        '''
            @summary: Called when a mode is set on the bot.
            @note: Used to trigger commands in queue requiring OP
        '''        
        super(self.__class__, self).on_bot_mode_set(channel)
    
    def on_recv_userhosts(self, nick, userhost):
        '''
            @param nick: The nick
            @param userhost: The nick's userhost
            @summary: Called when the a userhost is received
        '''
        super(self.__class__, self).on_recv_userhosts(nick, userhost)
    
    def on_userlist_complete(self, channel):
        '''            
            @param channel: The channel name
            @summary: Called when the the userlist has all entries completed
        '''
        if len(self._channels[channel]['members']):
            self.call_listeners('userlist', channel, None, self._channels[channel]['members'])
    
    # Persistence
    def save_state(self):
        '''
            @summary: Saves the state of the bot and the modules
        '''
        pickler = cPickle.Pickler(open('qirc.pkl', 'wb'))        
        pickler.dump(self._masters)                
        pickler.dump(self._extmgr.get_state())      # Dump Modules
        pickler.dump(self._cmdmgr.get_state())      # Dump Command Modules        
        
    
    def load_state(self):
        '''
            @summary: Loads the state of the bot and the modules
        '''
        if path.exists('qirc.pkl'):            
            pickler = cPickle.Unpickler(open('qirc.pkl', 'rb'))
            try:        
                # Load admins from config
                admins = self._masters['admin']['members']
                self._masters = pickler.load()
                # Combine both admins
                for a in admins:
                    if a not in self._masters['admin']['members']:
                        self._masters['admin']['members'].append(a)
                        
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
        (key, result, success) = self._cmdmgr.parse_line(None, user, cmd) or (None, None, None)
        if key:            
            if result:
                self.send_multiline(self.notice, user.nick, result.output)
        else:
            if success is None:
                if user.powers is None:
                    self.send(cmd)
                else:
                    self.notice(user.nick, 'You are not authorized to perform this operation. Type /msg %s help to see your list of commands' % self.config('bot', 'nick'))
        return True
    
    def parse_msg(self, channel, user, msg):
        '''
            @param role: The group of user
            @param nick: Nick of user
            @param host: Hostname of user
            @param msg: Message for bot
            @summary: Specifies additional rules as the general purpose responses
        '''
        Log.write("Parse Message %s" % msg)              
        _, result, success = self._extmgr.parse_line(channel, user, msg) or (None, None, None)            
        if not success:
            if result:
                self.send_multiline(self.notice, user.nick, result.output)                                                    
        elif result:
            self.say(channel, result.output)


# Use the final Bot as QircBot
QircBot = ArmageddonBot
'''    
    @version: 4.0
'''