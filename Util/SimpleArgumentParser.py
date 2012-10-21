'''
Created on Jul 15, 2012

@author: Nisheeth
'''

from argparse import ArgumentParser
from argparse import Action
from argparse import HelpFormatter

class ToggleAction(Action):
    '''
        Handles flags as arguments
    '''
    def __call__(self, parser, ns, values, option):
        setattr(ns, self.dest, bool("-+".index(option[0])))
       
class SimpleArgumentParser(ArgumentParser):
    '''
        Parses arguments using a custom formatter
    '''
    def __init__(self, *args, **kwargs):             
        suppress = kwargs.has_key('add_help') and kwargs['add_help'] is None
        kwargs.update({'add_help': False, 'formatter_class' : lambda prog: HelpFormatter(prog,max_help_position=30)})
        ArgumentParser.__init__(self, *args, **kwargs)        
        if not (suppress or self.add_help):
            self.add_help_argument("-h", "--help", action="store_true", help="Show this help message")
    
    def add_help_argument(self, *args, **kwargs):
        '''
            @note: Helps in adding additional help arguments
        '''
        self.help_args = args
        ArgumentParser.add_argument(self, *args, **kwargs)
        
    def error(self, message):
        '''
            @note: Overriden so as to prevent the program from terminating
        '''            
        raise Exception(message)
        pass   
    
    def add_flag(self, *args, **kwargs): 
        '''
            @summary: Adds a flag argument
        '''        
        kwargs.update({'action': ToggleAction, 'nargs': 0})        
        ArgumentParser.add_argument(self, *args, **kwargs)
        
    def parse_args(self, args=None, namespace=None):
        for arg in args:                # Stop if help is found
            idx = arg.rfind('-')
            if idx == 0 and len(arg) > 2:       # Composite single switches
                for a in arg[1:]:
                    if '-%s' % a in self.help_args:
                        raise StopIteration('help')
            elif idx != -1 and arg in self.help_args:
                raise StopIteration('help')
        namespace = ArgumentParser.parse_args(self, args, namespace)        
        return namespace