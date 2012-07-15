'''
Created on Jun 28, 2012

@author: Nisheeth
'''

from Util.SimpleOptionParser import SimpleOptionParser

class QircOptionParser(object):
    '''
        Defines the help modules and option parsers
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self._parsers = {
                # Commands
                #'flags'     : SimpleOptionParser(),
                # Actions
                'search'    : SimpleOptionParser(),
                'vote'      : SimpleOptionParser(),
                'define'    : SimpleOptionParser(),
                'calc'      : SimpleOptionParser(),
                'weather'   : SimpleOptionParser(),
                'locate'    : SimpleOptionParser(),
                'user'      : SimpleOptionParser(),
                'url'       : SimpleOptionParser(),
                'roll'      : SimpleOptionParser() 
            }
        
        #self._parsers['flags'].add_option("-v", "", action="store_false", dest="single", default=False, help="Output single line of title")        
        #self._parsers['flags'].check_args = False
        
        self._parsers['search'].add_option("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        self._parsers['search'].add_option("-t", "--result", type="int", dest="result", default=1, help="Get the N'th result", metavar="N")
        self._parsers['search'].add_option("-1", "--single", action="store_true", dest="single", default=False, help="Output single line of title")
        self._parsers['search'].add_option("-g", "--google", action="store_true", dest="google", default=True, help="Search on Google [Default]")
        self._parsers['search'].add_option("-i", "--gimage", action="store_true", dest="gimage", default=False, help="Search on Google Images")
        self._parsers['search'].add_option("-y", "--youtube", action="store_true", dest="youtube", default=False, help="Search on Youtube")
        self._parsers['search'].add_option("-w", "--wiki", action="store_true", dest="wiki", default=False, help="Search on Wikipedia")
        self._parsers['search'].add_option("-m", "--imdb", action="store_true", dest="imdb", default=False, help="Search on IMDB")
        self._parsers['search'].add_option("-f", "--tdf", action="store_true", dest="tdf", default=False, help="Search on TDF")
        self._parsers['search'].add_option("-c", "--custom", dest="custom", default=None, help="Search on a custom site")
        
        self._parsers['define'].add_option("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        self._parsers['define'].add_option("-t", "--result", type="int", dest="result", default=1, help="Get the N'th result", metavar="N")
        self._parsers['define'].add_option("-u", "--urban", action="store_true", dest="urban", default=True, help="Define using urbandictionary [Default]")
        self._parsers['define'].add_option("-g", "--google", action="store_true", dest="google", default=False, help="Define using google")
        self._parsers['define'].add_option("-d", "--dictionary", action="store_true", dest="dictionary", default=False, help="Define using dictionary.com")
        self._parsers['define'].add_option("-a", "--antonym", action="store_true", dest="antonym", default=False, help="Get antonym of word")
        self._parsers['define'].add_option("-e", "--etymology", action="store_true", dest="etymology", default=False, help="Get origin of word")
        
        self._parsers['vote'].add_option("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        self._parsers['vote'].add_option("-i", "--interval", type="int", dest="interval", default=15, help="Timeout interval N seconds", metavar="N")
        self._parsers['vote'].add_option("-k", "--kick", action="store_true", dest="kick", default=False, help="Kick the user")
        self._parsers['vote'].add_option("-a", "--arma", action="store_true", dest="arma", default=False, help="Bring forth armageddon upon user (kickban)")
        
        self._parsers['weather'].add_option("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        self._parsers['weather'].add_option("-f", "--forecast", action="store_true", dest="forecast", default=False, help="Forecast the weather")
        self._parsers['weather'].add_option("-d", "--days", type="int", dest="days", default=3, help="Forecast for N(max 3) days", metavar="N")
        self._parsers['weather'].check_args = False
        
        self._parsers['calc'].add_option("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        self._parsers['calc'].add_option("-w", "--wolf", action="store_true", dest="wolf", default=True, help="Calculate using wolfram alpha [Default]")
        self._parsers['calc'].add_option("-g", "--google", action="store_true", dest="google", default=False, help="Calculate using google calc")
        
        self._parsers['locate'].add_option("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        self._parsers['locate'].add_option("-i", "--ip", dest="ip", default=None, help="Locate using IP address", metavar="ABC.DEF.GHI.XYZ")
        self._parsers['locate'].add_option("-c", "--coord", dest="coord", default=None, help="Locate using latitude and logitude", metavar="LAT,LONG")                    
                        
        self._parsers['user'].add_option("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        self._parsers['user'].add_option("-s", "--seen", action="store_true", dest="seen", default=True, help="Check when a user was last seen")
        self._parsers['user'].add_option("-t", "--tell", dest="tell", help="Leave a message for the user", metavar="NICK")
        self._parsers['user'].add_option("-r", "--remind", dest="remind", help="Set a reminder for self", metavar="XX(d,h,m,s)")
        
        self._parsers['url'].add_option("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        self._parsers['url'].add_option("-d", "--dns", action="store_true", dest="dns", default=True, help="Perform DNS lookup on an url [Default]")
        self._parsers['url'].add_option("-t", "--title", action="store_true", dest="title", default=False, help="Fetch the url title")
        self._parsers['url'].add_option("-v", "--preview", action="store_true", dest="preview", default=False, help="Get a sneak peak into the page")
        self._parsers['url'].add_option("-c", "--content", action="store_true", dest="content", default=False, help="Gets the content type of the url")
        self._parsers['url'].add_option("-s", "--short", action="store_true", dest="short", default=False, help="Get the goo.gl short url")
        self._parsers['url'].add_option("-e", "--expand", action="store_true", dest="expand", default=False, help="Expand a goo.gl short url")        
        self._parsers['url'].add_option("-o", "--port", type="int", dest="port", help="Check if the port is open on a server", metavar="PORT")        
        
        self._parsers['roll'].add_option("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        self._parsers['roll'].add_option("-m", "--min", type="int", dest="min", default=1, help="Minimum range. Default %default", metavar="M")
        self._parsers['roll'].add_option("-n", "--max", type="int", dest="max", default=6, help="Maximum range. Default %default", metavar="N")
        self._parsers['roll'].check_args = False
        
        self._alias = {
                        's'    : 'search',
                        'c'    : 'calc',
                        'd'    : 'define',
                        'w'    : 'weather',
                        'l'    : 'locate',
                       }
        
    def parse(self, msg, args):
        if self._alias.has_key(msg):
            msg = self._alias[msg] 
        if not self._parsers.has_key(msg):
            return None, None, None
        try:
            (options, args) = self._parsers[msg].parse_args(args)                                 
        except:
            return msg, self._parsers[msg].format_help(), None               
        else:
            if self._parsers[msg].check_args and len(args) == 0:
                return (msg, 'Argument cannot be empty', None)
            else:
                return (msg, options, args)
            
    def get_help(self,msg):
        if self._alias.has_key(msg):
            msg = self._alias[msg]
        if self._parsers.has_key(msg):
            return self._parsers[msg].format_help()