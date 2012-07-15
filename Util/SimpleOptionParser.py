'''
Created on Jun 28, 2012

@author: Nisheeth
'''

from optparse import OptionParser
from optparse import Option
from optparse import HelpFormatter

class CleanIndentedHelpFormatter (HelpFormatter):
    '''
        Format help with indented section bodies and minimal text
    '''

    def __init__(self,
                 indent_increment=2,
                 max_help_position=24,
                 width=None,
                 short_first=1):
        HelpFormatter.__init__(self, indent_increment, max_help_position, width, short_first)
       
    def format_usage(self, usage):
        return "Options"

    def format_heading(self, heading):
        return ""
    
       
class OptionParsingError(RuntimeError):
    def __init__(self, msg):
        self.msg = msg

class OptionParsingExit(Exception):
    def __init__(self, status, msg):
        self.msg = msg
        self.status = status
                 
class SimpleOptionParser(OptionParser):
    '''
        Parses options using a custom formatter
    '''

    def __init__(self, usage=None,
                 option_list=None,
                 option_class=Option,
                 version=None,
                 conflict_handler="error",
                 description=None,
                 formatter=None,
                 add_help_option=True,
                 prog=None,
                 epilog=None):
        '''
        Constructor
        '''
        if formatter is None:
            formatter = CleanIndentedHelpFormatter()
        OptionParser.__init__(self, usage, option_list, option_class, version, conflict_handler, description, formatter, add_help_option, prog, epilog)
        self.check_args = True
        
    def _add_help_option(self):
        self.add_option("-h", "--help",
                        action="help",
                        help=("show this help message"))
        
    def print_help(self, file=None):
        """print_help(file : file = stdout)

        Print an extended help message, listing all options and any
        help text provided with them, to 'file' (default stdout).
        """
        pass
        
    
    def error(self, msg):
        raise OptionParsingError(msg)
    
    def exit(self, status=0, msg=None):        
        raise OptionParsingExit(status, msg)
        pass
