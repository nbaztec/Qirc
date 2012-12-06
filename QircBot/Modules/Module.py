'''
Created on Jul 30, 2012

@author: Nisheeth
'''
from abc import ABCMeta, abstractmethod
from QircBot.Interfaces.BotInterface import VerbalInterface, PrivilegedInterface
import re

class ModuleResult(object):
    '''
        Represents the result returned by modules
    '''
    def __init__(self, output=None):
        self.output = output       
        
class ModuleMetadata(object):
    '''
        Module Info
    '''
    def __init__(self):
        self._key = None
        self._prefixes = []
        self._aliases = []
        self._desc = ""
        self._listeners = []
        self._interface = VerbalInterface 
        
    @property
    def key(self):
        return self._key
    
    @property
    def prefixes(self):
        return self._prefixes
    
    @property
    def desc(self):
        return self._desc
    
    @property
    def aliases(self):
        return self._aliases
    
    @property
    def listeners(self):
        return self._listeners
    
    @property
    def interface(self):
        return self._interface
    
    @key.setter
    def key(self, value):
        self._key = value
    
    @prefixes.setter
    def prefixes(self, value):
        self._prefixes = value
        
    @desc.setter
    def desc(self, value):
        self._desc = value
    
    @aliases.setter
    def aliases(self, value):
        self._aliases = value
        
    @listeners.setter
    def listeners(self, value):
        self._listeners = value
    
    @interface.setter
    def interface(self, value):
        self._interface = value
    
    def regex_str(self):                
        if len(self._aliases):
            x = ''            
            for a in self._aliases:                
                x += re.escape(a)+'|'            
            if x: 
                x = x.rstrip('|')
                if len(self._prefixes):
                    return '[%s](?P<%s>%s)' % (re.escape(''.join(self._prefixes)), self._key, x);
                else:
                    return '(?P<%s>%s)' % (self._key, x);
        return None        
        
class CommandModuleMetadata(ModuleMetadata):
    '''
        Command Module Info
    '''
    def __init__(self):
        super(CommandModuleMetadata, self).__init__()
        self._interface = PrivilegedInterface
        self._prefixes = []
        
    def regex_str(self):
        if len(self._aliases):
            x = ''            
            for a in self._aliases:                
                x += re.escape(a)+'|'
            if x: 
                x = x.rstrip('|')
                if len(self._prefixes):
                    return '(?P<%s>%s)' % (self._key, x);
                else:
                    return '(?P<%s>%s)' % (self._key, x);
        return None 
    
class BaseModule(object):
    '''
        Base Module
    '''
    __metaclass__ = ABCMeta
           
    def __init__(self, interface):
        '''
            @param interface: An instance of BotInterface
        '''
        self._parser = self.build_parser()
        self._bot = interface;         
        
    @property
    def bot(self):
        return self._bot
    
    @property
    def parser(self):
        return self._parser
            
    def desc(self):
        return self._parser.format_help()
    
    @abstractmethod
    def build_parser(self):
        '''
            @note: Must return an instance of SimpleArgumentParser or None
        '''
        pass
    
    @abstractmethod
    def output(self, nick, host, auth, powers, options):
        pass
    
    def get_state(self):
        return None
    
    def set_state(self, state):
        return None
       
class BaseToggleModule(BaseModule):
    '''
        Base Toggle Module
    '''
    __metaclass__ = ABCMeta
           
    def __init__(self, interface):
        '''
            @param interface: An instance of BotInterface
        '''
        super(BaseToggleModule, self).__init__(interface)
        self._enabled = True        
        
    def enable(self):
        '''
            @return: True if status is changed, False if unchanged
        '''
        if self._enabled:
            return False
        else:
            self._enabled = True
            return True
    
    def disable(self):
        '''
            @return: True if status is changed, False if unchanged
        '''
        if self._enabled:
            self._enabled = False
            return True
        else:
            return False
        
    def is_enabled(self):
        return self._enabled    
    
    def get_state(self):
        return {'enabled': self._enabled}
    
    def set_state(self, state):        
        self._enabled = state['enabled']       
       
class BaseDynamicExtension(BaseToggleModule):
    '''
        Base Dynamic Extension
    '''
    __metaclass__ = ABCMeta           
   
    def __init__(self, bot_state):
        '''
            @param interface: An instance of BaseBot
        '''                        
        self._metadata = ModuleMetadata()
        self._metadata.key = None
        self.build_meta(self._metadata)     # Build Module
        super(BaseDynamicExtension, self).__init__(self._metadata.interface(bot_state))
        if "reload" not in self._metadata.listeners:            
            self._metadata.listeners.append("reload")
        
    @abstractmethod
    def build_meta(self, metadata):
        '''
            @summary: Returns a tuple representing the (command-name, command-alias-list)
        '''        
    
    @property
    def key(self):
        return self._metadata.key
    
    @property
    def aliases(self):
        return self._metadata.aliases
    
    @property
    def prefixes(self):
        return self._metadata.prefixes
    
    @property
    def desc(self):
        return self._metadata.desc
    
    @property
    def listeners(self):
        return self._metadata.listeners
    
    def get_regex_str(self):
        return self._metadata.regex_str()
        
    def get_interface_type(self):
        return self._metadata.interface

    def reload(self):
        pass
    
    def event(self, key, channel, user, args):
        '''
            @param key: A string identifying the listener
            @param channel: Channel name
            @param user: A User instance            
            @param args: Additional arguments, these may be either a list, a tuple of a string depending on the key
            
            @note: The description of various event types are given below
            
                   key         args
                   --------    ---------
                   motd_end    None
                   join        channel
                   part        reason
                   quit        reason
                   botquit     reason
                   exit        None
                   nick        new_nick
                   mode        (mode, flags, users)
                   msg         msg
                   privmsg     msg
                   broadcast   msg
                   notice      msg
                   kick        (source, reason)
                   ping        server
                   pong        (server, msg)
                   
        '''
        pass
    
    def build_parser(self):
        return None    
    
    def output(self, nick, host, auth, powers, options):
        pass
    
class BaseDynamicCommand(BaseDynamicExtension):
    '''
        Base Dynamic Command Module
    '''
    __metaclass__ = ABCMeta
    
    def __init__(self, bot_state):
        '''
            @param interface: An instance of BaseBot
        '''        
        self._metadata = CommandModuleMetadata()
        self._metadata.key = None
        self.build_meta(self._metadata)     # Build Module
        super(BaseDynamicExtension, self).__init__(self._metadata.interface(bot_state))
        if "privmsg" not in self._metadata.listeners:
            self._metadata.listeners.append("privmsg")
        if "reload" not in self._metadata.listeners:
            self._metadata.listeners.append("reload")
            
    