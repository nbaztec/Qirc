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
            self.add_argument("-h", "--help", action="store_true", help="Show this help message")
        self.check_args = True    
        
    def error(self, message):
        '''
            @note: Overriden so as to prevent the program from terminating
        '''  
        print message     
        raise Exception(message)
        pass   
    
    def add_flag(self, *args, **kwargs):         
        kwargs.update({'action': ToggleAction, 'nargs': 0})        
        ArgumentParser.add_argument(self, *args, **kwargs)
        
    def parse_args(self, args=None, namespace=None, help_dest='help'):
        namespace = ArgumentParser.parse_args(self, args, namespace)
        if hasattr(namespace, help_dest) and getattr(namespace, help_dest):
            raise Exception('help')
        return namespace
        
        