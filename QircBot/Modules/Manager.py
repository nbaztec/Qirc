'''
Created on Jul 30, 2012
Updated on Oct 16, 2012
@author: Nisheeth
'''

from Util.Log import Log
import shlex
import re
from Module import ModuleResult

class BaseManager(object):
    '''
        Base Manager for Modules
    '''
    def __init__(self):
        self._modules = {}
        self._aliases = {}
        self._stage = {}
    
    def get_current_module_state(self, key):
        '''
            @param key: String representing the module
            @return: The current state dict of the module 
        '''        
        if self._modules.has_key(key):
            return self._modules[key].get_state()        
        
    def get_module_state(self, key):
        '''
            @param key: String representing the module
            @return: The state dict of the module 
        '''        
        if self._stage.has_key(key):
            return self._stage[key]
    
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
            @param state: State of the manager
            @summary: Sets the state of this object
        '''
        self._stage = state
            
    def set_module_state(self, key, state):
        '''
            @param key: String representing the module
            @param state: State of the manager
            @summary: Sets the state_dict of the module
        '''        
        self._stage[key] = state
        
    def add(self, key, module, aliases=None):
        '''
            @param key: An identifier for module
            @param module: An instance of type BaseModule
            @param enabled: Enable the module
            @param aliases: List of aliases, if any 
            @summary: Adds the module to the manager
        '''
        self._modules[key] = module
        if aliases is not None:
            for a in aliases:
                self._aliases[a] = key
        # Persistence
        s = self.get_module_state(key)          
        if s:
            try:
                module.set_state(s)                 # Load the modules previous state
            except:
                Log.error('Error restoring state for %s. Have you changed the class structure? : ' % key)
    
    def remove(self, key):
        '''
            @param key: An identifier for module
            @summary: Removes the module from the manager
        '''        
        self._modules.pop(key)
        if self._stage.has_key(key):
            self._stage.pop(key)
        for a, m in self._aliases.items():
            if m == key:
                self._aliases.pop(a)            
    
    def clear(self):
        '''
            @summary: Removes all the modules from the manager
        '''
        self._modules = {}
        self._aliases = {}
        self._stage = None
                    
    def exists(self, key):
        '''
            @param key: An identifier for module
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
            @param key: An identifier for module
            @return: The module
        '''
        return self._modules[key]
    
    def is_enabled(self, key):
        '''
            @param key: An identifier for module
            @return: True if module is enabled
        '''
        return self._modules[key].is_enabled()
    
    def enable_module(self, key):
        '''
            @param key: An identifier for module
            @summary: Enables the module
        '''
        self._modules[key].enable()
    
    def disable_module(self, key):
        '''
            @param key: An identifier for module
            @summary: Disables the module
        '''
        self._modules[key].disable()
        
    def help(self, key):
        '''
            @param key: An identifier for module
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
            @param nick: User's nick
            @param host: User's hostmask
            @param auth: User's authorization level
            @param powers: User's powers
            @param args: The argument string specified by the user
            @summary: Enabled the module
        '''
        pass
    
    def arg_split(self, args):
        '''
            @param args: The argument string
            @return: List of tokens
            @summary: Splits a string as done by a shell
        '''
        lex = shlex.shlex(args, posix=True)
        lex.quotes = '"'
        lex.escape = ''
        lex.commenters = ''
        lex.whitespace_split = True
        return list(lex)

class ListenerManager(object):
    '''
        ListenerManager for handling event dispatch
    '''
    
    def __init__(self):        
        self._listeners = {}
        
    def call_listeners(self, key, channel, user, line):
        '''
            @summary: Calls the listener on all modules registered for it
        '''
        if self._listeners.has_key(key):            
            for o in self._listeners[key]:
                try:
                    if o.event(key, channel, user, line):
                        break
                except Exception, e:
                    Log.error('Error in extension "%s" for key "%s": %s' % (o.key, key, e))
            return True
        else:
            return False
        
    def call_listener(self, key, mod_key, channel, user, line):
        '''
            @param mod_key: A string identifying the module
            @summary: Calls the listener for a particular modules registered for it
        '''
        if self._listeners.has_key(key):
            for o in self._listeners[key]:
                try:
                    if o.key == mod_key:
                        o.event(key, channel, user, line)
                        break
                except Exception, e:
                    Log.error('Error in extension "%s" for key "%s": %s' % (o.key, key, e))
            return True
        else:
            return False
    
    def attach_listeners(self, keys, obj):
        '''
            @param keys: A list of listener keys
            @param obj: The BaseDynamicModule instance to assign to listeners
            @summary: Attaches a module to all the specified listeners
        '''
        for key in keys:
            if self._listeners.has_key(key):
                self._listeners[key].append(obj)
            else:
                self._listeners[key] = [obj]
            
    def remove_listener(self, key, obj):
        '''
            @param key: A string identifying the listener
            @param obj: The BaseDynamicModule instance to remove
            @summary: Removes a module from the specified listener
        '''        
        if obj in self._listeners[key]:
            self._listeners[key].remove(obj)
            if len(self._listeners[key]) == 0:
                self._listeners.pop(key)            
    
    def purge_listeners(self, obj):
        '''           
            @param obj: The BaseDynamicModule instance to purge
            @summary: Removes the module from all listeners
        '''
        for key, l in self._listeners.items():
            if obj in l:
                l.remove(obj)
                if len(l) == 0:
                    self._listeners.pop(key)


class DynamicExtensionManager(BaseManager, ListenerManager):
    '''
        Manages Dynamic Extensions
    '''
    def __init__(self):        
        BaseManager.__init__(self)
        ListenerManager.__init__(self)
        self._modregex = None               # Regex to match module key in the command string
        self._modregex_str = ''
        pass
                
    @property
    def modregex(self):
        return self._modregex
    
    @property
    def modregex_str(self):
        return self._modregex_str
    
    def reload(self, key=None):
        '''
            @summary: Calls reload on each module
        '''
        if key:
            self._modules[key].reload()
        else:
            for m in self._modules.values():
                m.reload()
    
    def build_regex(self, regex_str=None):
        '''
            @param regex_str: If specified the string is set as the regex instead of building the string from modules
        '''
        if regex_str:
            r = regex_str
        else:
            r = ''
            for m in self._modules.values():
                rxs = m.get_regex_str()
                if rxs:
                    r += rxs + '|'
            r = r.rstrip('|')
            
        if len(r):
            r = '^(?:%s)(?:\s|$)' % r
            self._modregex = re.compile(r)
            self._modregex_str = r
        else:
            self._modregex = None
            self._modregex_str = ''
             
    def add(self, module, rebuild=True):
        '''
            @param module: An instance of type BaseDynamicModule
            @param rebuild: True if the regex matcher should be built after attaching, False if build_regex() will be called explicitly
            @summary: Adds the module to the manager
        '''
        if self._modules.has_key(module.key):
            removed = True
            self.remove(module.key)
        else:
            removed = False
            
        self._modules[module.key] = module
        if module.aliases is not None:
            for a in module.aliases:
                self._aliases[a] = module.key
        # Persistence
        s = self.get_module_state(module.key)
        if s:
            module.set_state(s)                 # Load the modules previous state
        if rebuild:
            self.build_regex()
            
        # Attach Listeners
        self.attach_listeners(module.listeners, module)
        
        return removed
    
    def remove(self, key, rebuild=True):
        '''
            @param key: An identifier for module
            @param rebuild: True if the regex matcher should be re-built after removing, False if build_regex() will be called explicitly
            @summary: Removes the module from the manager
        '''
        # Purge Listeners
        if self._modules.has_key(key):
            self.purge_listeners(self._modules[key])
            super(DynamicExtensionManager, self).remove(key)        
            if rebuild:
                self.build_regex()
            return True
    
    def enabled_modules(self):
        l = []
        for k, m in self._modules.items():
            if m.is_enabled():
                l.append(k)
        return l
    
    def disabled_modules(self):
        l = []
        for k, m in self._modules.items():
            if not m.is_enabled():
                l.append(k)
        return l
    
    def clear(self):
        '''
            Removes all modules from the manager
        '''
        for key in self._modules.keys():
            self.remove(key, False)
        self._modregex = None
        self._modregex_str = ''
    
    def check(self, user, line):
        '''
            @summary: Checks a line for a command and returns the result of the parse
        '''
        m = self._modregex.match(line)
        if m and m.lastgroup:
            return m.lastgroup, line[m.end(m.lastgroup)+1:]
        else:    
            return (None, None)
                    
    def parse(self, channel, user, key, args):
        '''
            @param key: A string identifying the module
            @summary: Parses the command for the specified module
        '''
        if not self.exists(key):
            return (None, None, None)
        elif self.is_enabled(key):
            parser = self._modules[key].parser        
            try:
                args = self.arg_split(args)
                return key, self._modules[key].output(channel, user, parser.parse_args(args)), True
            except ValueError, e:
                Log.error("ParserError: %s" % e.message)
                return key, ModuleResult("Parser Error '%s': %s" % (key, e)), False
            except StopIteration, e:    # help requested
                return key, ModuleResult(parser.format_help()), False
            except Exception, e:    
                Log.error("ArgumentError: %s" % e)
                return key, ModuleResult("Argument Error '%s': %s. Use -h/--help to get help on the parameters" % (key, e)), False 
        else:
            return key, ModuleResult("Module is disabled"), False
    
    def parse_line(self, channel, user, line):
        '''
            @summary: Checks a line for a command and returns the result of the parse
        '''
        
        key, args = self.check(user, line)        
        return self.parse(channel, user, key, args)
        
class DynamicCommandManager(DynamicExtensionManager):
    '''
        Manages Dynamic Modules
    '''
    
    def __init__(self):
        super(DynamicCommandManager, self).__init__()
    
    def call_listeners(self, key, channel, user, line):
        '''
            @summary: Calls the listener on all modules registered for it
        '''
        #if (key != 'privmsg' or user.powers is None or key in user.powers) and self._listeners.has_key(key):
        if self._listeners.has_key(key):
            for o in self._listeners[key]:
                try:
                    if o.event(key, channel, user, line):
                        break
                except Exception, e:
                    Log.error('Error in %s: %s' % (o.key, e))
            return True
        else:
            return False
                    
    def parse(self, channel, user, key, args):
        '''
            @param key: A string identifying the module
            @summary: Parses the command for the specified module
        '''        
        if not self.exists(key):
            return (None, None, None)
        elif self.is_enabled(key):
            if user.powers is None or key in user.powers:
                parser = self._modules[key].parser        
                try:
                    args = self.arg_split(args)
                    return key, self._modules[key].output(channel, user, parser.parse_args(args)), True
                except ValueError, e:
                    Log.error("ParserError: %s" % e.message)
                    return key, ModuleResult('Parser Error: %s' % e), False
                except StopIteration, e:    # help requested
                    return key, ModuleResult(parser.format_help()), False
                except Exception, e:    
                    Log.error("ArgumentError: %s" % e)
                    return key, ModuleResult('Argument Error: %s. Use -h/--help to get help on the parameters' % e), False
            else:
                (None, None, None) 
        else:
            return key, ModuleResult("Module is disabled"), False
    