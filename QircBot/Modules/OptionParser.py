'''
Created on Jun 28, 2012

@author: Nisheeth
'''

#from Util.SimpleOptionParser import SimpleOptionParser
import shlex
from Util.SimpleArgumentParser import SimpleArgumentParser
SimpleOptionParser = SimpleArgumentParser

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
                'join'      : SimpleOptionParser(prog="join"),
                'quit'      : SimpleOptionParser(prog="quit"),
                'enforce'   : SimpleOptionParser(prog="enforce"),
                'kick'      : SimpleOptionParser(prog="kick"),
                'ban'       : SimpleOptionParser(prog="ban"),
                'op'        : SimpleOptionParser(prog="op"),
                'say'       : SimpleOptionParser(prog="say"),
                'armageddon': SimpleOptionParser(prog="armageddon"),
                'flags'     : SimpleOptionParser(prog="flags", prefix_chars="+-", add_help=None, usage="flags [--help] +/-[hvlkbat]"),                
                
                # Actions
                'search'    : SimpleOptionParser(prog="!search"),
                'vote'      : SimpleOptionParser(prog="!vote"),
                'define'    : SimpleOptionParser(prog="!define"),
                'calc'      : SimpleOptionParser(prog="!calc"),
                'weather'   : SimpleOptionParser(prog="!weather"),
                'locate'    : SimpleOptionParser(prog="!locate"),
                'user'      : SimpleOptionParser(prog="!user"),
                'url'       : SimpleOptionParser(prog="!url"),
                'roll'      : SimpleOptionParser(prog="!roll"),
                'game'      : SimpleOptionParser(prog="!game"), 
            }
        
        self._parsers['join'].add_argument("chan", help="Join a channel", metavar="CHANNEL")
             
        self._parsers['quit'].add_argument("-r", "--restart", action="store_true", dest="restart", default=False, help="Restart bot")
        self._parsers['quit'].add_argument("msg", nargs="*", help="Quit message", metavar="MESSAGE")
                
        self._parsers['enforce'].add_argument("-k", "--kick", dest="kick", action="store_true", help="Enforce a kick [Default]")
        self._parsers['enforce'].add_argument("-b", "--ban", dest="ban", action="store_true", help="Enforce a ban")
        self._parsers['enforce'].add_argument("-l", "--list", dest="list", action="store_true", help="List rules")
        self._parsers['enforce'].add_argument("-r", "--remove", dest="remove", action="store_true", help="Remove rule")
        self._parsers['enforce'].add_argument("-e", "--regex", dest="regex", action="store_true", help="Rule is a regex")
        self._parsers['enforce'].add_argument("rule", nargs="*", help="Match rule", metavar="RULE")
        
        self._parsers['kick'].add_argument("-r", "--reason", dest="reason", help="Kick reason")
        self._parsers['kick'].add_argument("nicks", nargs="+", help="Nicks of users", metavar="NICKS")
        
        self._parsers['ban'].add_argument("-r", "--remove", dest="remove", help="Remove ban")        
        self._parsers['ban'].add_argument("nicks", nargs="+", help="Nicks of users", metavar="NICKS")
        
        self._parsers['op'].add_argument("-r", "--remove", dest="remove", action="store_true", default=False, help="Deop user")
        self._parsers['op'].add_argument("chan", nargs="?", help="Channel", metavar="CHANNEL")
        self._parsers['op'].add_argument("nick", nargs="?", help="Nicks of users", metavar="NICK")
        
        self._parsers['say'].add_argument("-w", "--whisper", dest="notice", help="Whisper to user", metavar="NICK")
        self._parsers['say'].add_argument("-s", "--self", dest="me", help="Speak to self")
        self._parsers['say'].add_argument("-m", "--privmsg", dest="privmsg", help="Message to channel or user", metavar="NICK")        
        self._parsers['say'].add_argument("msg", nargs="+", help="Message", metavar="MESSAGE")
        
        self._parsers['armageddon'].add_argument("-u", "--users", nargs="*", dest="users", help="Selective users to arma", metavar="NICK")
        self._parsers['armageddon'].add_argument("-r", "--recover", dest="recover", action="store_true", default=False, help="Unban all users banned in last armageddon")
        
        self._parsers['flags'].add_argument("--help", action="store_true", dest="help", default=False, help="Show this help")                
        self._parsers['flags'].add_flag("+h", "-h", dest="hear", help="Hear commands")
        self._parsers['flags'].add_flag("+v", "-v", dest="voice", help="Voice results")
        self._parsers['flags'].add_flag("+l", "-l", dest="log", help="Enable logging")
        self._parsers['flags'].add_flag("+k", "-k", dest="kick", help="Allow kicking")
        self._parsers['flags'].add_flag("+b", "-b", dest="ban", help="Allow banning")
        self._parsers['flags'].add_flag("+a", "-a", dest="arma", help="Allow armageddon (kickban)")
        self._parsers['flags'].add_flag("+t", "-t", dest="talk", help="Allow talking")                                
        
        # ACTIONS
        self._parsers['search'].add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        self._parsers['search'].add_argument("-t", "--result", type=int, dest="result", default=1, help="Get the N'th result", metavar="N")
        self._parsers['search'].add_argument("-1", "--single", action="store_true", dest="single", default=False, help="Output single line of title")
        group = self._parsers['search'].add_mutually_exclusive_group()
        group.add_argument("-g", "--google", action="store_true", dest="google", default=True, help="Search on Google [Default]")
        group.add_argument("-i", "--gimage", action="store_true", dest="gimage", default=False, help="Search on Google Images")
        group.add_argument("-y", "--youtube", action="store_true", dest="youtube", default=False, help="Search on Youtube")
        group.add_argument("-w", "--wiki", action="store_true", dest="wiki", default=False, help="Search on Wikipedia")
        group.add_argument("-m", "--imdb", action="store_true", dest="imdb", default=False, help="Search on IMDB")
        group.add_argument("-f", "--tdf", action="store_true", dest="tdf", default=False, help="Search on TDF")
        group.add_argument("-c", "--custom", dest="custom", default=None, help="Search on a custom site")
        self._parsers['search'].add_argument("args", nargs="+", help="Search query", metavar="query")
        
        self._parsers['define'].add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        self._parsers['define'].add_argument("-t", "--result", type=int, dest="result", default=1, help="Get the N'th result", metavar="N")
        group = self._parsers['define'].add_mutually_exclusive_group()
        group.add_argument("-u", "--urban", action="store_true", dest="urban", default=True, help="Define using urbandictionary [Default]")
        group.add_argument("-g", "--google", action="store_true", dest="google", default=False, help="Define using google")
        group.add_argument("-d", "--dictionary", action="store_true", dest="dictionary", default=False, help="Define using dictionary.com")
        group.add_argument("-a", "--antonym", action="store_true", dest="antonym", default=False, help="Get antonym of word")
        group.add_argument("-e", "--etymology", action="store_true", dest="etymology", default=False, help="Get origin of word")
        self._parsers['define'].add_argument("args", nargs="+", help="Query term", metavar="term")
        
        #self._parsers['vote'].add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        group = self._parsers['vote'].add_mutually_exclusive_group() 
        self._parsers['vote'].add_argument("-i", "--interval", type=int, dest="interval", default=15, help="Timeout interval N seconds", metavar="N")
        group.add_argument("-k", "--kick", action="store_true", dest="kick", default=False, help="Kick the user")
        group.add_argument("-a", "--arma", action="store_true", dest="arma", default=False, help="Bring forth armageddon upon user (kickban)")
        self._parsers['vote'].add_argument("args", nargs="+", help="Vote question or reason", metavar="question")
        
        self._parsers['weather'].add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        self._parsers['weather'].add_argument("-f", "--forecast", action="store_true", dest="forecast", default=False, help="Forecast the weather")
        self._parsers['weather'].add_argument("-d", "--days", type=int, dest="days", choices=[1,2,3], default=3, help="Forecast for N(max 3) days")
        self._parsers['weather'].add_argument("args", nargs="+", help="Name of location", metavar="place")
        
        self._parsers['calc'].add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        group = self._parsers['calc'].add_mutually_exclusive_group()
        group.add_argument("-w", "--wolf", action="store_true", dest="wolf", default=True, help="Calculate using wolfram alpha [Default]")
        group.add_argument("-g", "--google", action="store_true", dest="google", default=False, help="Calculate using google calc")
        self._parsers['calc'].add_argument("args", nargs="+", help="Calculation to perform", metavar="calculation")
        
        self._parsers['locate'].add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        group = self._parsers['locate'].add_mutually_exclusive_group()
        group.add_argument("-i", "--ip", dest="ip", default=None, help="Locate using IP address", metavar="ABC.DEF.GHI.XYZ")
        group.add_argument("-c", "--coord", dest="coord", default=None, help="Locate using latitude and logitude", metavar="LAT,LONG")                    
                        
        self._parsers['user'].add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        group = self._parsers['user'].add_mutually_exclusive_group()
        group.add_argument("-s", "--seen", action="store_true", dest="seen", default=True, help="Check when a user was last seen")
        group.add_argument("-t", "--tell", dest="tell", help="Leave a message for the user", metavar="MESSAGE")
        group.add_argument("-r", "--remind", dest="remind", help="Set a reminder for self", metavar="XX(d,h,m,s)")
        self._parsers['user'].add_argument("args", nargs="+", help="User's nick", metavar="nick")
        
        self._parsers['url'].add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        group = self._parsers['url'].add_mutually_exclusive_group()
        group.add_argument("-d", "--dns", action="store_true", dest="dns", default=True, help="Perform DNS lookup on an url [Default]")
        group.add_argument("-t", "--title", action="store_true", dest="title", default=False, help="Fetch the url title")
        group.add_argument("-v", "--preview", action="store_true", dest="preview", default=False, help="Get a sneak peak into the page")
        group.add_argument("-c", "--content", action="store_true", dest="content", default=False, help="Gets the content type of the url")
        group.add_argument("-s", "--short", action="store_true", dest="short", default=False, help="Get the goo.gl short url")
        group.add_argument("-e", "--expand", action="store_true", dest="expand", default=False, help="Expand a goo.gl short url")        
        group.add_argument("-o", "--port", type=int, dest="port", help="Check if the port is open on a server", metavar="PORT")
        self._parsers['url'].add_argument("args", help="URL or a relative reference", metavar="[url|%{1-5}]")        
        
        self._parsers['roll'].add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        self._parsers['roll'].add_argument("-m", "--min", type=int, dest="min", default=1, help="Minimum range. Default %default", metavar="M")
        self._parsers['roll'].add_argument("-n", "--max", type=int, dest="max", default=6, help="Maximum range. Default %default", metavar="N")
        
        self._parsers['game'].add_argument("args", choices={"werewolf"}, help="Name of the game")
        
        
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
            args = shlex.split(args)
            return msg, self._parsers[msg].parse_args(args), True
        except:
        #except Exception, e:
            #print "E",e
            return msg, self._parsers[msg].format_help(), False
            
    def get_help(self,msg):
        if self._alias.has_key(msg):
            msg = self._alias[msg]
        if self._parsers.has_key(msg):
            return self._parsers[msg].format_help()
        
    def split(self, cmd, esc=['"', "'"]):
        quote = False
        args = []
        arg = ''
        for c in cmd:
            if c in esc:
                quote = not quote
            elif c == ' ':
                if quote:
                    arg += c
                else:
                    args.append(arg)
                    arg = ''
            else:
                arg += c
        if arg != '':
            args.append(arg)
        return args