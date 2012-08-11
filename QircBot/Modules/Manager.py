'''
Created on Jul 30, 2012

@author: Nisheeth
'''
import shlex
from Module import ModuleResult

class User(object):
    '''
        Keeps information about a user
    '''
    def __init__(self, nick, name, host, auth, level, powers):
        self._nick =  nick
        self._name = name
        self._host = host
        self._auth = auth
        self._level = level
        self._powers = powers
        
    @property
    def nick(self):
        return self._nick
    
    @property
    def username(self):
        return self._name
    
    @property
    def hostname(self):
        return self._host
    
    @property
    def authority(self):
        return self._auth
    
    @property
    def level(self):
        return self._level
    
    @property
    def powers(self):
        return self._powers
    
    @property
    def fullname(self):
        return '%s!%s@%s' % (self._name, self._name, self._host) 
    
class BaseManager(object):
    '''
        Base Manager for Modules
    '''
    def __init__(self):
        self._modules = {}
        self._aliases = {}
        self._state = None
    
    def get_module_state(self, key):
        '''
            @var key: String representing the module
            @return: The state dict of the module 
        '''
        if self._state and self._state.has_key(key):
            return self._state[key]
    
    def get_state(self):
        '''
            @return: The state dict of manager 
        '''
        state = {}
        for k, v in self._modules.items():
            state[k] = v.get_state()
        return state
    
    def set_state(self, state):
        '''
            @var state: State of the manager
            @summary: Sets the state of this object
        '''
        self._state = state
            
    def add(self, key, module, aliases=None):
        '''
            @var key: An identifier for module
            @var module: An instance of type BaseModule
            @var enabled: Enable the module
            @var aliases: List of aliases, if any 
            @summary: Adds the module to the manager
        '''
        self._modules[key] = module
        if aliases is not None:
            for a in aliases:
                self._aliases[a] = key
        # Persistence
        s = self.get_module_state(key)          
        if s:
            module.set_state(s)                 # Load the modules previous state
    
    def remove(self, key):
        '''
            @var key: An identifier for module
            @summary: Removes the module from the manager
        '''
        self._modules.pop(key)
        for a, m in self._aliases:
            if m == key:
                self._aliases.pop(a)
        
    def exists(self, key):
        '''
            @var key: An identifier for module
            @return: True if module exists            
        '''
        return self._modules.has_key(key)
    
    def modules(self):
        '''
            @return: The (key, value) pair of modules
        '''
        return self._modules.items()
    
    def module(self, key):
        '''
            @var key: An identifier for module
            @return: The module
        '''
        return self._modules[key]
    
    def is_enabled(self, key):
        '''
            @var key: An identifier for module
            @return: True if module is enabled
        '''
        return self._modules[key].is_enabled()
    
    def enable_module(self, key):
        '''
            @var key: An identifier for module
            @summary: Enables the module
        '''
        self._modules[key].enable()
    
    def disable_module(self, key):
        '''
            @var key: An identifier for module
            @summary: Disables the module
        '''
        self._modules[key].disable()
        
    def help(self, key):
        '''
            @var key: An identifier for module
            @return: Help on the module
        '''
        if self._aliases.has_key(key):
            key = self._aliases[key]        
        if not self.exists(key):
            return None
        else:
            return self._modules[key].help()

    def parse(self, nick, host, auth, powers, key, args):      
        '''
            @var nick: User's nick
            @var host: User's hostmask
            @var auth: User's authorization level
            @var powers: User's powers
            @var args: The argument string specified by the user
            @summary: Enabled the module
        '''
        pass
    
    def arg_split(self, args):
        '''
            @var args: The argument string
            @return: List of tokens
            @summary: Splits a string as done by a shell
        '''
        lex = shlex.shlex(args, posix=True)
        lex.escape = ''
        lex.whitespace_split = True
        return list(lex)

class ModuleManager(BaseManager):
    '''
        Manager Modules
    '''
    def __init__(self):
        BaseManager.__init__(self)
        self._intelligence = []
        pass
        
    def add_intelligence(self, module):
        '''
            @var module: Instance of BaseModule
            @summary: Adds an intelligence module 
        '''
        self._intelligence.append(module)
                
    def parse(self, nick, host, auth, powers, key, args):        
        if self._aliases.has_key(key):
            key = self._aliases[key]
        if not self.exists(key):
            return None, None, None
        elif self.is_enabled(key):
            parser = self._modules[key].parser        
            try:
                args = self.arg_split(args)
                return key, self._modules[key].output(nick, host, auth, powers, parser.parse_args(args)), True
            except Exception, e:
                print "Error", e
                return key, ModuleResult(parser.format_help()), False
        else:
            return key, ModuleResult("Module is disabled"), False
                
    def reply(self, nick, host, auth, powers, args):
        '''
            @var nick: User's nick
            @var host: User's hostmask
            @var auth: User's authorization level
            @var powers: User's powers
            @var args: The argument string specified by the user
            @summary: Uses intelligence modules to reply
        '''
        for intelli in self._intelligence:
            if intelli.output(nick, host, auth, powers, args):
                break
                   
class CommandManager(BaseManager):
    '''
        Manages Command Modules
    '''    
    def parse(self, nick, host, auth, powers, key, args):
        if self._aliases.has_key(key):
            key = self._aliases[key]
        if not self.exists(key):
            return None, None, None
        else:#if self.is_enabled(key):
            parser = self._modules[key].parser        
            try:
                args = self.arg_split(args)
                return key, self._modules[key].output(nick, host, auth, powers, parser.parse_args(args)), True
            except Exception, e:
                print "Error", e
                return key, ModuleResult(parser.format_help()), False
        #else:
        #    return key, ModuleResult("Command is disabled"), False