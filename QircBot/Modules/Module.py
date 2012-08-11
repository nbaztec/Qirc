'''
Created on Jul 30, 2012

@author: Nisheeth
'''
from abc import ABCMeta, abstractmethod

class BaseModule(object):
    '''
        Base Module
    '''
    __metaclass__ = ABCMeta
           
    def __init__(self, interface):
        '''
            @var interface: An instance of BotInterface
        '''
        self._parser = self.build_parser()
        self._bot = interface; 
        
    @property
    def bot(self):
        return self._bot
    
    @property
    def parser(self):
        return self._parser
            
    def help(self):
        return self._parser.format_help()
    
    @abstractmethod
    def build_parser(self):
        '''
            @note: Must return an instance of SimpleArgumentParser
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
            @var interface: An instance of BotInterface
        '''
        super(BaseToggleModule, self).__init__(interface)
        self._enabled = True        
        
    def enable(self):
        self._enabled = True
    
    def disable(self):
        self._enabled = False
        
    def is_enabled(self):
        return self._enabled    
    
    def get_state(self):
        return {'enabled': self._enabled}
    
    def set_state(self, state):
        self._enabled = state['enabled']
       
class ModuleResult(object):
    '''
        Represents the result returned by modules
    '''
    def __init__(self, output=None):
        self.output = output        
        
        
        