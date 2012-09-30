'''
Created on Jul 30, 2012

@author: Nisheeth
'''
from Module import BaseToggleModule, ModuleResult
from Util.SimpleArgumentParser import SimpleArgumentParser
from Extensions import Search, Calc, Define, Weather, Locate, Url, Roll
from Extensions.Vote import VoteMaster
from Extensions.User import Tell, Remind, Seen
from Extensions.Game import Werewolf
from Extensions.AI import PseudoIntelligence, CleverBot
from Util import htmlx
import re

class SearchModule(BaseToggleModule):
    '''
        Module for performing searches
    '''
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!search")
        parser.add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        parser.add_argument("-t", "--result", type=int, dest="result", default=1, help="Get the N'th result", metavar="N")
        parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", help="Output textual descriptions")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-g", "--google", action="store_true", dest="google", default=True, help="Search on Google [Default]")
        group.add_argument("-i", "--gimage", action="store_true", dest="gimage", default=False, help="Search on Google Images")
        group.add_argument("-y", "--youtube", action="store_true", dest="youtube", default=False, help="Search on Youtube")
        group.add_argument("-w", "--wiki", action="store_true", dest="wiki", default=False, help="Search on Wikipedia")
        group.add_argument("-m", "--imdb", action="store_true", dest="imdb", default=False, help="Search on IMDB")
        group.add_argument("-f", "--tdf", action="store_true", dest="tdf", default=False, help="Search on TDF")
        group.add_argument("-c", "--custom", dest="custom", default=None, help="Search on a custom site")
        parser.add_argument("args", nargs="+", help="Search query", metavar="query")        
        return parser
        
    def output(self, nick, host, auth, powers, options):              
        args = ' '.join(options.args)                
        single = not options.verbose
        if options.custom:
            r = Search.customsearch(args, options.custom, options.result, single)              
        elif options.gimage:
            r = Search.googleimage(args, options.result, single)
        elif options.youtube:
            r = Search.youtube(args, options.result, single)
        elif options.wiki:
            r = Search.wiki(args, options.result, single)
        elif options.imdb:
            r = Search.imdb(args, options.result, single)
        elif options.tdf:
            r = Search.tdf(args, options.result, single)
        elif options.google:
            r = Search.google(args, options.result, single)
        else:
            r = "No results for you"
        
        if r:
            if options.private:
                self._bot.notice(nick, r)
            else:
                return ModuleResult('%s, %s' % (r, nick))   
        

class CalculationModule(BaseToggleModule):
    '''
        Module for performing calculations
    '''
    
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!calc")
        parser.add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-w", "--wolf", action="store_true", dest="wolf", default=True, help="Calculate using wolfram alpha [Default]")
        group.add_argument("-g", "--google", action="store_true", dest="google", default=False, help="Calculate using google calc")
        parser.add_argument("args", nargs="+", help="Calculation to perform", metavar="calculation")        
        return parser
        
    def output(self, nick, host, auth, powers, options):              
        args = ' '.join(options.args)
        if options.google:
            r = Calc.googlecalc(args)
        elif options.wolf:
            r = Calc.wolfram(args)
        else:
            r = "I can't solve that"
        if r:
            if options.private:
                self._bot.notice(nick, r)
            else:
                return ModuleResult('%s, %s' % (r, nick))
        

class DefinitionModule(BaseToggleModule):
    '''
        Module for performing word operations
    '''
    
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!define")
        parser.add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        parser.add_argument("-t", "--result", type=int, dest="result", default=1, help="Get the N'th result", metavar="N")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-u", "--urban", action="store_true", dest="urban", default=True, help="Define using urbandictionary [Default]")
        group.add_argument("-g", "--google", action="store_true", dest="google", default=False, help="Define using google")
        group.add_argument("-d", "--dictionary", action="store_true", dest="dictionary", default=False, help="Define using abbreviations.com")
        group.add_argument("-s", "--synonym", action="store_true", dest="synonym", default=False, help="Get synonyms of a word")
        #group.add_argument("-e", "--etymology", action="store_true", dest="etymology", default=False, help="Get origin of word")
        parser.add_argument("args", nargs="+", help="Query term", metavar="term")
        return parser
        
    def output(self, nick, host, auth, powers, options):              
        args = ' '.join(options.args)                     
        if options.google:
            r = Define.googledefine(args, options.result)
        elif options.dictionary:
            r = Define.dictionary(args, options.result)
        elif options.synonym:
            r = Define.synonyms(args, options.result)
        #elif options.antonym:
        #    pass                                        # TODO: Antonym
        #elif options.etymology:
        #    pass                                        # TODO: Etymology
        elif options.urban:
            r = Define.urbandefine(args, options.result)
        if r:            
            if options.private:
                self._bot.notice(nick, r.replace('\r', ' '))
            else:
                return ModuleResult('%s, %s' % (r.replace('\r', ' '), nick))
            
class QuoteModule(BaseToggleModule):
    '''
        Module for performing word operations
    '''
    
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!quote")
        parser.add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        parser.add_argument("-t", "--result", type=int, dest="result", default=1, help="Get the N'th result", metavar="N")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-r", "--random", action="store_true", dest="random", default=True, help="Get a random quote[Default]")
        group.add_argument("-a", "--author", dest="author", nargs="+", default=None, help="Search a quote by the author", metavar="AUTHOR")
        group.add_argument("-s", "--search", dest="search", nargs="+", default=None, help="Search a quote by contents", metavar="TERM")        
        return parser
        
    def output(self, nick, host, auth, powers, options):
        r = None                                          
        if options.author:
            r = Define.quote(' '.join(options.author), author=True, num=options.result)
        elif options.search:
            r = Define.quote(' '.join(options.search), search=True, num=options.result)
        elif options.random:
            r = Define.quote('random', num=options.result)        
        if r:            
            if options.private:
                self._bot.notice(nick, r.replace('\r', ' '))
            else:
                return ModuleResult('%s' % r.replace('\r', ' '))
        
class WeatherModule(BaseToggleModule):
    '''
        Module for performing weather operations
    '''
    
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!weather")
        parser.add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        parser.add_argument("-f", "--forecast", action="store_true", dest="forecast", default=False, help="Forecast the weather")
        parser.add_argument("-d", "--days", type=int, dest="days", choices=[1,2,3], default=3, help="Forecast for N(max 3) days")
        parser.add_argument("args", nargs="+", help="Name of location", metavar="place")
        return parser
        
    def output(self, nick, host, auth, powers, options):              
        args = ' '.join(options.args)
        if options.forecast:
            r = Weather.forecast(args, options.days)
        else:
            r = Weather.weather(args)
        if r:
            if options.private:
                self._bot.notice(nick, r)
            else:
                return ModuleResult('%s, %s' % (r, nick))
        
class LocationModule(BaseToggleModule):
    '''
        Module for performing location based operations
    '''
    
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!locate")
        parser.add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-i", "--ip", dest="ip", default=None, help="Locate using IP address", metavar="ABC.DEF.GHI.XYZ")
        group.add_argument("-c", "--coord", dest="coord", default=None, help="Locate using latitude and logitude", metavar="LAT,LONG") 
        return parser
        
    def output(self, nick, host, auth, powers, options):              
        if options.ip:
            r = Locate.iplocate(options.ip)
        elif options.coord:
            l = options.coord.split(',')
            r = Locate.geo(l[0], l[1])
        if r:
            if options.private:
                self._bot.notice(nick, r)
            else:
                return ModuleResult('%s, %s' % (r, nick))
        
class UrlModule(BaseToggleModule):
    '''
        Module for performing url operations
    '''
    def __init__(self, interface):
        BaseToggleModule.__init__(self, interface)
        self._last5urls = []
        self._regex_url = re.compile(r'\b((?:telnet|ftp|rtsp|https?)://[^/]+[-\w_/?=%&+;#\\@.]*)')
    
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!url", prefix_chars="+-")
        parser.add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        group = parser.add_mutually_exclusive_group()        
        group.add_argument("-d", "--dns", action="store_true", dest="dns", default=True, help="Perform DNS lookup on an url [Default]")
        group.add_argument("-t", "--title", action="store_true", dest="title", default=False, help="Fetch the url title")
        group.add_argument("-v", "--preview", action="store_true", dest="preview", default=False, help="Get a sneak peak into the page")
        group.add_argument("-c", "--content", action="store_true", dest="content", default=False, help="Gets the content type of the url")
        group.add_argument("-s", "--short", action="store_true", dest="short", default=False, help="Get the goo.gl short url")
        group.add_argument("-e", "--expand", action="store_true", dest="expand", default=False, help="Expand a goo.gl short url")        
        group.add_argument("-o", "--port", type=int, dest="port", help="Check if the port is open on a server", metavar="PORT")
        parser.add_argument("args", help="URL or a relative reference", metavar="[url|%{1-5}]")        
        return parser
        
    def output(self, nick, host, auth, powers, options):              
        args = options.args                            
        try:                                
            m = re.match(r'^%(\d)$', args)                            
            if m:
                args = self._last5urls[int(m.group(1))-1]                                                                       
        except Exception:
            r = None
            self._bot.notice(nick, 'No url exists for %' + m.group(1))            
        else:            
            if args.find('://', 0, 10) == -1:
                args = 'http://' + args
            if options.title:
                r = Url.title(args)
            elif options.content:
                r = Url.content_type(args)
            elif options.preview:
                r = Url.description(args)
            elif options.short:
                r = Url.googleshort(args)
            elif options.expand:
                r = Url.googleexpand(args)
            elif options.port:
                r = Url.port(args, options.port)
            elif options.dns:                            
                r = Url.dns(args)            
        if r:
            if options.private:
                self._bot.notice(nick, r)
            else:
                return ModuleResult('%s, %s' % (r, nick))
        
    def append_if_url(self, msg):        
        '''
            @var msg: 
        '''
        m = self._regex_url.search(msg)
        if m is not None:
            if len(self._last5urls) == 5:
                self._last5urls.pop()
            self._last5urls.insert(0, m.group(0))
            if self._bot.has_status('url'):
                r = Url.title(m.group(0), only_title=True)
                if r:
                    self._bot.say(r)
        
    def get_state(self):    
        d =  super(UrlModule, self).get_state()
        d.update({ 'urls' : self._last5urls})        
        return d
    
    def set_state(self, state):
        self._last5urls = state['urls']
        super(UrlModule, self).set_state(state)
        
class UserModule(BaseToggleModule):
    '''
        Module for performing word operations
    '''
    def __init__(self, interface, sqlite_db):
        BaseToggleModule.__init__(self, interface)
        self._tell = Tell()
        self._remind = Remind(self._bot.say)
        self._seen = Seen(sqlite_db)
    
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!user")
        parser.add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-c", "--clear", action="store_true", dest="clear", help="Clear messages for 'remind' or 'tell' [Admin]")
        group.add_argument("-s", "--seen", dest="seen", action="store_true", default=True, help="Check when a user was last seen [Default]")
        group.add_argument("-t", "--tell", dest="tell", help="Leave a message for the user", metavar="USER")
        group.add_argument("-r", "--remind", dest="remind", help="Set a reminder for self", metavar="XX(d,h,m,s)")
        parser.add_argument("args", nargs="+", help="Message", metavar="MESSAGE")
        return parser
        
    def output(self, nick, host, auth, powers, options):
        if auth == 0 and options.clear:            
            if options.args[0] == "tell":
                self._bot.notice(nick, '%d message(s) were dropped' % self._tell.clear())
            elif options.args[0] == "remind":
                self._bot.notice(nick, '%d reminder(s) were dropped' % self._remind.clear())
            else:
                self._bot.notice(nick, 'Please specify either "remind" or "tell"')
        elif options.tell:               
            if len(options.args):
                self._tell.post(nick, options.tell, ' '.join(options.args))
                self._bot.notice(nick, 'Ok, I will convey the message to %s' % options.tell)
            else:
                self._bot.notice(nick, 'Atleast specify a message :/')
        elif options.remind:   
            try:             
                arg = ' '.join(options.args)      
                self._remind.remind(nick, options.remind, arg)
                self._bot.notice(nick, 'Reminder has been set')
            except Remind.RemindFormatError:
                self._bot.notice(nick, 'Invalid time format. Example 20s, 2m, 3h...')
            except Remind.RemindValueError, e:
                self._bot.notice(nick, e.message)
        elif options.seen:                  
            for usr in options.args:
                if usr == self._bot.botnick:
                    r = "Me? Surely you ca't be serious"
                else:
                    r = self._seen.seen(usr)
                if r:
                    if options.private:
                        self._bot.notice(nick, r)
                    else:
                        return ModuleResult('%s, %s' % (r, nick))
                    
    def tell_get(self, nick):
        return self._tell.get(nick)
    
    def seen_join(self, nick, ident, host):
        self._seen.join(nick, ident, host)
        
    def seen_part(self, nick, reason):
        self._seen.part(nick, reason)
        
    def remind_dispose(self):
        self._remind.dispose()
        
    def get_state(self):
        d = super(UserModule, self).get_state()        
        d.update({    'tell' : self._tell.get_state(),
                    'remind': self._remind.get_state()
                })
        return d
    
    def set_state(self, state):
        self._tell.set_state(state['tell'])
        self._remind.set_state(state['remind'])
        super(UserModule, self).set_state(state)

class VoteModule(BaseToggleModule):
    '''
        Module for performing voting
    '''
    def __init__(self, interface):
        BaseToggleModule.__init__(self, interface)
        self._vote = VoteMaster()
    
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!vote")
        group = parser.add_mutually_exclusive_group() 
        parser.add_argument("-i", "--interval", type=int, dest="interval", default=15, help="Timeout interval N seconds (min 5)", metavar="N")
        group.add_argument("-k", "--kick", action="store_true", dest="kick", default=False, help="Kick the user")
        group.add_argument("-a", "--arma", action="store_true", dest="arma", default=False, help="Bring forth armageddon upon user (kickban)")
        parser.add_argument("args", nargs="+", help="Vote question or reason", metavar="question")
        return parser
        
    def output(self, nick, host, auth, powers, options):              
        if options.kick:                
            if auth < 3:                    
                msg_u = options.args
                kick_users = msg_u[0]
                kick_reason = ' '.join(msg_u[1:])                    
                # Define callback                    
                def vote_result(p, n, q):                                        
                    if (p+n) > 1:
                        vote = p - n
                        if vote > 0:                        
                            self._bot.say('The general public (%d) has agreed to kick %s' % (p + n, kick_users))
                            for u in kick_users.split():
                                self._bot.kick(u, kick_reason)
                        elif vote < 0:                        
                            self._bot.say('The general public (%d) has disagreed to kick %s' % (p + n, kick_users))
                        else:
                            self._bot.say('The outcome is a draw! %s is/are saved.' % kick_users)
                    else:
                        self._bot.say('A minimum of 2 votes are required for taking decision.')
                # Call
                self._vote.start(options.interval, 'kick %s %s' % (kick_users, kick_reason), self._bot.say, vote_result)                
        elif options.arma:          
            #args = ' '.join(options.args)                                                              
            if auth < 3:                                
                # Define calback
                arma_users = options.args[0]
                arma_reason = ' '.join(options.args[1:])
                def vote_result(p, n, q):
                    if (p+n) > 1:
                        vote = p - n
                        if vote > 0:
                            self._bot.say('The general public (%d) has agreed to bring forth armageddon upon %s' % (p + n, arma_users))                            
                            self._bot.kickban(arma_users.split())
                        elif vote < 0:
                            self._bot.say('The general public (%d) has disagreed to bring forth armageddon upon %s' % (p + n, arma_users))
                        else:
                            self._bot.say('The outcome is a draw! %s is/are saved.' % arma_users)
                    else:
                        self._bot.say('A minimum of 2 votes are required for taking decision.')
                # Call    
                self._vote.start(options.interval, 'Bring forth armageddon upon %s? (%s)' % (arma_users, arma_reason), self._bot.say, vote_result)                
        else:                                       # Regular vote
            args = ' '.join(options.args)
            def vote_result(p, n, q):
                vote = p - n
                if vote:
                    self._bot.say('The general public (%d) %s : %s' % ((p + n), 'agrees' if vote > 0 else 'disagrees', q))
                else:
                    self._bot.say('The outcome is a draw! Bummer.')
            self._vote.start(options.interval, args, self._bot.say, vote_result)
    
    @property
    def is_voting(self):
        return self._vote.is_voting    
    
    def register_vote(self, nick, host, vote):
        self._vote.register_vote(nick, host, vote)
        
class RollModule(BaseToggleModule):
    '''
        Module for performing word operations
    '''
    
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!roll")
        parser.add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        parser.add_argument("-m", "--min", type=int, dest="min", default=1, help="Minimum range. Default %(default)s", metavar="M")
        parser.add_argument("-n", "--max", type=int, dest="max", default=6, help="Maximum range. Default %(default)s", metavar="N")
        return parser
        
    def output(self, nick, host, auth, powers, options):              
        if options.min > 0 and options.max > 0 and options.min < options.max:
            r = Roll.roll(options.min, options.max)
        else:
            self._bot.notice(nick, 'Roll limits are weird, mate')
            r = None
        if r:
            if options.private:
                self._bot.notice(nick, r)
            else:
                return ModuleResult('%s rolled a %s' % (nick, r))    
        
class GameModule(BaseToggleModule):
    '''
        Module for performing word operations
    '''
    def __init__(self, interface):
        BaseToggleModule.__init__(self, interface)
        self._werewolf = Werewolf(callback=self._bot.say, pm=self._bot.notice)
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!game")
        parser.add_argument("args", choices=["werewolf"], help="Name of the game")
        return parser
        
    def output(self, nick, host, auth, powers, options):              
        args = ' '.join(options.args)
        if args == 'werewolf':
            self._werewolf.start()
            #r = 'Game is currently offline'       
    
    @property
    def is_joining(self):
        return self._werewolf.is_joining
    
    @property
    def is_playing(self):
        return self._werewolf.is_playing
    
    @property
    def is_running(self):
        return self._werewolf.is_running
    
    def join(self, nick):
        self._werewolf.join(nick) 
        
    def response(self, nick, msg):
        m = re.search(r'\+ ?([\S]*)', msg)
        if m:
            self._werewolf.lynch(nick, m.group(1))
            
              
class VerbModule(BaseToggleModule):
    '''
        Module for performing verb related actions
    '''
    
    def __init__(self, interface):
        BaseToggleModule.__init__(self, interface)
        self._regex_action = re.compile(r'^\s*([\S]+)(?:\s+([\S]+))(?:\s+(.*))?')        
        
    def build_parser(self):
        return None
        
    def output(self, nick, host, auth, powers, options):           
        m = self._regex_action.search(options)
        if m:
            return self.parse_verb(m.group(1), m.group(2), m.group(3))
        
    def parse_verb(self, verb, nick, text):
        '''
            @var verb: The action text
            @var nick: The nick part
            @var text: The text message
            @summary: Parses verbs to present action for the bot 
        '''                
        if verb in ['dodge', 'give', 'steal', 'take', 'catch', 'arm', 'engage', 'assault', 'launch', 'slit', 'poke', 'strip', 'disarm', 'fire', 'attack', 'chase', 'create', 'make', 'relieve', 'show', 'escort', 'push', 'pull', 'throw', 'feed', 'fuck', 'sell', 'buy', 'oblige', 'demolish', 'destroy']:
            verb += 'es' if verb.endswith(('s', 'z', 'x', 'sh', 'ch'), -2) else 's'            
            if nick is not None:
                if text is None:
                    text = ''
                self._bot.action('%s %s %s' % (verb, nick, text))                
        elif verb == 'slap':
            self._bot.action('bitchslaps %s' % (nick))       
        else:
            return False 
        return True
    
class CleverModule(BaseToggleModule):
    '''
        Module for performing word operations
    '''
    def __init__(self, interface, nick):
        BaseToggleModule.__init__(self, interface)
        self._intelli = PseudoIntelligence()    # AI module, Work in development                      
        self._cb = CleverBot({'name': nick})
                    
    def build_parser(self):
        return None
        
    def output(self, nick, host, auth, powers, options):                    
        reply = self._intelli.reply(options, nick)                      # Use AI for replying
        if not reply:  
            reply = self._cb.ask(options)
        if reply:                                                       # If there's some valid reply                  
            reply = htmlx.unescape(reply)
            self._bot.say(reply)                                        # Use AI for replying
            return True
        else:
            return False