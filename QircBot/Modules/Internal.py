'''
Created on Jul 30, 2012

@author: Nisheeth
'''
from QircBot.Interfaces.BotInterface import EnforcerInterface, PrivilegedInterface
from Module import BaseDynamicExtension, ModuleResult
from Util.SimpleArgumentParser import SimpleArgumentParser
from Extensions import Search, Calc, Define, Weather, Locate, Url, Roll, User, Vote, Game, AI, Timer, Twitter
from Util import Chronograph
from Util import htmlx

from datetime import datetime
import re

class HelpModule(BaseDynamicExtension):
    '''
        Extension for displaying help
    '''
    def build_meta(self, metadata):
        metadata.key = "help"
        metadata.aliases = ["help"]
        metadata.prefixes = ["!"]
        metadata.desc = "Show this help"
        metadata.interface = PrivilegedInterface
    
    def build_parser(self):
        return SimpleArgumentParser(prog="!help")
        
    def output(self, channel, user, options):
        max_len = 1
        l = [] 
        for _, v in self._bot.modules():
            if len(v.aliases):
                p = ''.join(v.prefixes)
                if len(p) > 1:
                    p = '[%s]' % p
                p = '%s%s' % (p, (', '+p).join(v.aliases))
                if len(p) > max_len:
                    max_len = len(p)
                l.append((p, v.desc))
        s = ''
        for m in l:
            s += ('%-' + str(max_len+2) + 's%s\n') % m
        self._bot.send_multiline(self._bot.notice, user.nick, s.rstrip())
            
class SearchModule(BaseDynamicExtension):
    '''
        Extension for performing searches
    '''        
        
    def build_meta(self, metadata):
        metadata.key = "search"
        metadata.aliases = ["search", "s", "g"]
        metadata.prefixes = ["!"]
        metadata.desc = "Search for a term on various sites"
                
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
    
    def reload(self):
        reload(Search)
        
    def output(self, channel, user, options):              
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
                self._bot.notice(user.nick, r)
            else:
                return ModuleResult('%s , %s' % (r, user.nick))      # Space introduced because some clients use comma as URL-part as per RFC3986    
        

class CalculationModule(BaseDynamicExtension):
    '''
        Extension for performing calculations
    '''
    def build_meta(self, metadata):
        metadata.key = "calc"
        metadata.aliases = ["calc", "c"]
        metadata.prefixes = ["!"]
        metadata.desc = "Perform some calculation"
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!calc")
        parser.add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-w", "--wolf", action="store_true", dest="wolf", default=True, help="Calculate using wolfram alpha [Default]")
        group.add_argument("-g", "--google", action="store_true", dest="google", default=False, help="Calculate using google calc")
        parser.add_argument("args", nargs="+", help="Calculation to perform", metavar="calculation")        
        return parser
    
    def reload(self):
        reload(Calc)
        
    def output(self, channel, user, options):              
        args = ' '.join(options.args)
        if options.google:
            r = Calc.googlecalc(args)
        elif options.wolf:
            r = Calc.wolfram(args)
        else:
            r = "I can't solve that"
        if r:
            if options.private:
                self._bot.notice(user.nick, r)
            else:
                return ModuleResult('%s, %s' % (r, user.nick))
        

class DefinitionModule(BaseDynamicExtension):
    '''
        Extension for performing word operations
    '''
    def build_meta(self, metadata):
        metadata.key = "define"
        metadata.aliases = ["define", "urban", "d"]
        metadata.prefixes = ["!"]
        metadata.desc = "Get the meaning, antonyms, etc. for a term"
        
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
    
    def reload(self):
        reload(Define)
        
    def output(self, channel, user, options):              
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
                self._bot.notice(user.nick, r.replace('\r', ' '))
            else:
                return ModuleResult('%s, %s' % (r.replace('\r', ' '), user.nick))
            
class QuoteModule(BaseDynamicExtension):
    '''
        Extension for performing word operations
    '''
    def build_meta(self, metadata):
        metadata.key = "quote"
        metadata.aliases = ["quote", "q"]
        metadata.prefixes = ["!"]
        metadata.desc = "Search for a quote"
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!quote")
        parser.add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        parser.add_argument("-t", "--result", type=int, dest="result", default=1, help="Get the N'th result", metavar="N")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-r", "--random", action="store_true", dest="random", default=True, help="Get a random quote[Default]")
        group.add_argument("-a", "--author", dest="author", nargs="+", default=None, help="Search a quote by the author", metavar="AUTHOR")
        group.add_argument("-s", "--search", dest="search", nargs="+", default=None, help="Search a quote by contents", metavar="TERM")        
        return parser
    
    def reload(self):
        reload(Define)
        
    def output(self, channel, user, options):
        r = None                                          
        if options.author:
            r = Define.quote(' '.join(options.author), author=True, num=options.result)
        elif options.search:
            r = Define.quote(' '.join(options.search), search=True, num=options.result)
        elif options.random:
            r = Define.quote('random', num=options.result)        
        if r:            
            if options.private:
                self._bot.notice(user.nick, r.replace('\r', ' '))
            else:
                return ModuleResult('%s' % r.replace('\r', ' '))
        
class WeatherModule(BaseDynamicExtension):
    '''
        Extension for performing weather operations
    '''
    def build_meta(self, metadata):
        metadata.key = "weather"
        metadata.aliases = ["weather", "w"]
        metadata.prefixes = ["!"]
        metadata.desc = "Get weather forecasts for a location"
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!weather")
        parser.add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        parser.add_argument("-f", "--forecast", action="store_true", dest="forecast", default=False, help="Forecast the weather")
        parser.add_argument("-d", "--days", type=int, dest="days", choices=[1,2,3], default=3, help="Forecast for N(max 3) days")
        parser.add_argument("args", nargs="+", help="Name of location", metavar="place")
        return parser
    
    def reload(self):
        reload(Weather)
        
    def output(self, channel, user, options):              
        args = ' '.join(options.args)
        if options.forecast:
            r = Weather.forecast(args, options.days)
        else:
            r = Weather.weather(args)
        if r:
            if options.private:
                self._bot.notice(user.nick, r)
            else:
                return ModuleResult('%s, %s' % (r, user.nick))
        
class LocationModule(BaseDynamicExtension):
    '''
        Extension for performing location based operations
    '''
    def build_meta(self, metadata):
        metadata.key = "location"
        metadata.aliases = ["locate", "l"]
        metadata.prefixes = ["!"]
        metadata.desc = "Locate an IP or coordinate"
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!locate")
        parser.add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-i", "--ip", dest="ip", default=None, help="Locate using IP address", metavar="ABC.DEF.GHI.XYZ")
        group.add_argument("-c", "--coord", dest="coord", default=None, help="Locate using latitude and logitude", metavar="LAT,LONG") 
        return parser
    
    def reload(self):
        reload(Locate)
        
    def output(self, channel, user, options):              
        if options.ip:
            r = Locate.iplocate(options.ip)
        elif options.coord:
            l = options.coord.split(',')
            r = Locate.geo(l[0], l[1])
        if r:
            if options.private:
                self._bot.notice(user.nick, r)
            else:
                return ModuleResult('%s, %s' % (r, user.nick))
        
class UrlModule(BaseDynamicExtension):
    '''
        Extension for performing url operations
    '''    
    
    def __init__(self, interface):
        super(UrlModule, self).__init__(interface)        
        self._last5urls = {}
        # Naive url matcher
        #self._regex_url = re.compile(r'\b((?:telnet|ftp|rtsp|https?)://[^/]+[-\w_/?=%&+;#\\@.]*)')
        
        # Use this RFC Compliant-ish regex instead
        #self._regex_url = re.compile(r"\b(?:telnet|file|ftp|rtsp|https?)://([\w;:&=+$,%-_.!~*'()]+@)?[-\w.]+(:\d+)?(/[-\w;_.!~*'()%:@&=+$,/]+)?(\?[-\w;/?:@&=+$,_.!~*'()%]+)?(\#[-\w;/?:@&=+$,_.!~*'()%]+)?")
        
        # This one skips delimeters at end
        self._regex_url = re.compile(r"\b(?:telnet|file|[ts]?ftp|ftps?|irc|rtsp|https?)://([\w;:&=+$,%-_.!~*'()]+@)?[-\w.]+(:\d+)?(/[-\w;_.!~*'()%:@&=+$,/]*)?(\?[-\w;/?:@&=+$,_.!~*'()%]+)?(\#[-\w;/?:@&=+$,_.!~*'()%]+)?[\w/]")
        
    def build_meta(self, metadata):
        metadata.key = "url"
        metadata.aliases = ["url"]
        metadata.prefixes = ["!"]
        metadata.listeners = ["msg", "action", "botpart"]
        metadata.desc = "Perform operation on an url"
        
    def event(self, key, channel, user, args):
        if key == "msg" or key == "action":            
            self.append_if_url(channel, args)                       # Check for URL
        elif key == "botpart":
            if self._last5urls.has_key(channel):
                self._last5urls.pop(channel)
    
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!url", prefix_chars="+-")
        parser.add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-l", "--list", action="store_true", dest="list", default=False, help="Print the url")        
        group.add_argument("-d", "--dns", action="store_true", dest="dns", default=True, help="Perform DNS lookup on an url [Default]")
        group.add_argument("-t", "--title", action="store_true", dest="title", default=False, help="Fetch the url title")
        group.add_argument("-v", "--preview", action="store_true", dest="preview", default=False, help="Get a sneak peak into the page")
        group.add_argument("-c", "--content", action="store_true", dest="content", default=False, help="Gets the content type of the url")
        group.add_argument("-s", "--short", action="store_true", dest="short", default=False, help="Get the goo.gl short url")
        group.add_argument("-e", "--expand", action="store_true", dest="expand", default=False, help="Expand a goo.gl short url")        
        group.add_argument("-o", "--port", type=int, dest="port", help="Check if the port is open on a server", metavar="PORT")
        parser.add_argument("args", help="URL or a relative reference", metavar="[url|%{1-5}]")        
        return parser
    
    def reload(self):
        reload(Url)
        
    def output(self, channel, user, options):              
        args = options.args                            
        try:                                
            m = re.match(r'^%(\d)$', args)                            
            if m:
                args = self._last5urls[channel][int(m.group(1))-1]                                                                       
        except Exception:
            r = None
            self._bot.notice(user.nick, 'No url exists for %' + m.group(1))            
        else:            
            if args.find('://', 0, 10) == -1:
                args = 'http://' + args
            if options.list:
                r = args
            elif options.title:
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
                self._bot.notice(user.nick, r)
            else:
                return ModuleResult('%s, %s' % (r, user.nick))
        
    def append_if_url(self, channel, msg):        
        '''
            @param msg: 
        '''
        m = self._regex_url.search(msg)
        if m is not None:
            if not self._last5urls.has_key(channel):
                self._last5urls[channel] = []
            sz = len(self._last5urls[channel])
            if sz == 5:
                self._last5urls[channel].pop()
            if sz == 0 or (sz and self._last5urls[channel][0] != m.group(0)):
                self._last5urls[channel].insert(0, m.group(0))
                if self._bot.has_status('url'):
                    r = Url.title(m.group(0), only_title=True)
                    if r:
                        self._bot.say(channel, r)
        
    def get_state(self):
        d = super(self.__class__, self).get_state()
        d.update({ 'urls' : self._last5urls})        
        return d
    
    def set_state(self, state):
        self._last5urls = state['urls']
        super(self.__class__, self).set_state(state)
        
class UserModule(BaseDynamicExtension):
    '''
        Extension for performing word operations
    '''    
    
    def __init__(self, bot_state):
        super(UserModule, self).__init__(bot_state)
        self._tell = User.Tell()
        self._remind = User.Remind(self._bot.say)
        self._seen = User.Seen(self._bot.sqlite_db)
    
    def build_meta(self, metadata):
        metadata.key = "user"
        metadata.aliases = ["user"]
        metadata.prefixes = ["!"]
        metadata.desc = "Perform operation related to user"
        metadata.interface = EnforcerInterface
        metadata.listeners = ["msg", "action", "userlist", "join", "kick", "part", "quit", "exit", "botpart"]
        
    def event(self, key, channel, user, args):
        if key == "msg" or key == "action":
            messages = self.tell_get(channel, user.nick)
            if messages:
                for sender, msg, timestamp in messages:
                    self._bot.say(channel, '%s, %s said (%s ago) "%s"' % (user.nick, sender, Chronograph.time_ago(timestamp), msg))
        elif key == "join":            
            self.seen_join(channel, user.nick, user.ident, user.host)
        elif key == "kick":      
            self.seen_part(channel, user.nick, user.ident, user.host, "Kicked by %s, Reason: %s" % (args[0], args[1]))
        elif key == "part":            
            self.seen_part(channel, user.nick, user.ident, user.host, "Parted: %s" % args)
        elif key == "quit":            
            self.seen_part(channel, user.nick, user.ident, user.host, args)
        elif key == "userlist":            
            self.seen_init(channel, args)
        elif key == "exit" or key == "reload":
            self.remind_dispose()
        elif key == "botpart":
            self._remind.clear(channel, pop=True)
            self._tell.clear(channel, pop=True)
    
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
    
    def reload(self):
        reload(User)
        
    def output(self, channel, user, options):
        if user.auth == 0 and options.clear:            
            if options.args[0] == "tell":
                self._bot.notice(user.nick, '%d message(s) were dropped' % self._tell.clear(channel))
            elif options.args[0] == "remind":
                self._bot.notice(user.nick, '%d reminder(s) were dropped' % self._remind.clear(channel))
            else:
                self._bot.notice(user.nick, 'Please specify either "remind" or "tell"')
        elif options.tell:               
            if len(options.args):
                self._tell.post(channel, user.nick, options.tell, ' '.join(options.args))
                self._bot.notice(user.nick, 'Ok, I will convey the message to %s' % options.tell)
            else:
                self._bot.notice(user.nick, 'Atleast specify a message :/')
        elif options.remind:   
            try:             
                arg = ' '.join(options.args)      
                self._remind.remind(channel, user.nick, options.remind, arg)
                self._bot.notice(user.nick, 'Reminder has been set')
            except User.RemindFormatError:
                self._bot.notice(user.nick, 'Invalid time format. Example 20s, 2m, 3h...')
            except User.RemindValueError, e:
                self._bot.notice(user.nick, e.message)
        elif options.seen:                  
            for usr in options.args:
                if usr == self._bot.nick:
                    r = "Me? Surely you can't be serious"
                else:                    
                    nicks, userstring, timestamp, quit_reason = self._seen.seen(channel, usr)
                    disp_name = userstring#usr
                    if nicks is None:
                        r = "No I haven't seen %s lately" % usr 
                    else:                        
                        if usr in nicks:
                            nicks.remove(usr)
                                                   
                        all_nicks = ', '.join(nicks)
                        if quit_reason is None:                            
                            if self._bot.members(channel).has_key(usr):
                                if str(self._bot.members(channel)[usr]) != userstring:
                                    r = '%s is impersonating %s [%s] at the moment' % (self._bot.members(channel)[usr], disp_name, all_nicks)
                                else:
                                    r = '%s [%s] is right here' % (usr, all_nicks)
                            else:
                                k = None
                                for n in nicks:
                                    if self._bot.members(channel).has_key(n):
                                        k = n
                                        break
                                if k:
                                    r = '%s [%s] is right here under the nick %s' % (disp_name, all_nicks, k)
                                else:
                                    r = '%s [%s] was last seen joining %s ago, but he\'s not here now' % (disp_name, all_nicks, Chronograph.time_ago(datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')))
                        else:                         
                            r = '%s [%s] was last seen: %s ago (%s)' % (disp_name, all_nicks, Chronograph.time_ago(datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')), quit_reason)
                    
                if r:
                    if options.private:
                        self._bot.notice(user.nick, r)
                    else:
                        return ModuleResult('%s, %s' % (r, user.nick))
                    
    def tell_get(self, channel, nick):
        return self._tell.get(channel, nick)
    
    def seen_init(self, channel, members):
        self._seen.init(channel, members)
        
    def seen_join(self, channel, nick, ident, host):
        self._seen.join(channel, nick, ident, host)
        
    def seen_part(self, channel, nick, ident, host, reason):
        self._seen.part(channel, nick, ident, host, reason)
        
    def remind_dispose(self):
        self._remind.dispose()
        
    def get_state(self):
        d = super(self.__class__, self).get_state()        
        d.update({    'tell' : self._tell.get_state(),
                    'remind': self._remind.get_state()
                })
        return d
    
    def set_state(self, state):
        self._tell.set_state(state['tell'])
        self._remind.set_state(state['remind'])
        super(self.__class__, self).set_state(state)

class VoteModule(BaseDynamicExtension):
    '''
        Extension for performing voting
    '''
    
    def __init__(self, interface):
        super(VoteModule, self).__init__(interface)
        self._vote = Vote.VoteMaster()
        self._timer = Timer.Timer()
        
    def build_meta(self, metadata):
        metadata.key = "vote"
        metadata.aliases = ["vote"]
        metadata.prefixes = ["!"]
        metadata.desc = "Start a vote"
        metadata.interface = EnforcerInterface
        metadata.listeners = ["msg", "exit", "reload"]
    
    def reload(self):
        reload(Vote)
        reload(Timer)
        
    def event(self, key, channel, user, args):
        if key == "msg":            
            if self.is_voting(channel):
                if len(args) == 1:
                    self.register_vote(channel, user.nick, user.host, args)
                    return True     # Supress this event
        elif key == "exit" or key == "reload":
            self._timer.dispose()
            
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!vote")
        group = parser.add_mutually_exclusive_group() 
        parser.add_argument("-i", "--interval", type=int, dest="interval", default=15, help="Timeout interval N seconds (min 5)", metavar="N")
        parser.add_argument("-t", "--timeout", dest="timeout", default=None, help="Timeout for unbanning user (min: 15s)", metavar="N")
        parser.add_argument("-c", "--clear", action="store_true", dest="clear", default=False, help="Clear all pending timeout actions")
        group.add_argument("-k", "--kick", dest="kick", nargs="+", default=None, help="Kick the user")
        group.add_argument("-a", "--arma", dest="arma", nargs="+", default=None, help="Bring forth armageddon upon user (kickban)")        
        parser.add_argument("args", nargs="+", help="Vote question or reason", metavar="question")
        return parser
        
    def output(self, channel, user, options):
        if options.clear:
            if options.args[0] == 'timeout':
                self._bot.say(channel, 'Dropped %d timeout action(s)' % self._timer.clear())
        elif options.kick:                
            if user.auth <= 150:
                kick_users = ', '.join(options.kick)
                kick_reason = ' '.join(options.args)
                # Define callback                    
                def vote_result(c, p, n, q):                                        
                    if (p+n) > 1:
                        vote = p - n
                        if vote > 0:                        
                            self._bot.say(c, 'The general public (%d) has agreed to kick %s' % (p + n, kick_users))
                            for u in options.kick:
                                self._bot.kick(c, u, kick_reason)
                        elif vote < 0:                        
                            self._bot.say(c, 'The general public (%d) has disagreed to kick %s' % (p + n, kick_users))
                        else:
                            self._bot.say(c, 'The outcome is a draw! %s is/are saved.' % kick_users)
                    else:
                        self._bot.say(c, 'A minimum of 2 votes are required for taking decision.')
                # Call
                self._vote.start(channel, options.interval, 'kick %s? (%s)' % (kick_users, kick_reason), self._bot.say, vote_result)                
        elif options.arma:          
            #args = ' '.join(options.args)                                                              
            if user.auth <= 50:                                
                # Define calback
                kb_users = ', '.join(options.arma)
                kb_reason = ' '.join(options.args)
                #kb_users = options.args[0]
                #kb_reason = ' '.join(options.args[1:])
                try:
                    kb_timeout = self._timer.parse_time(options.timeout) if options.timeout else None
                    def vote_result(c, p, n, q):                        
                        if (p+n) > 1:
                            vote = p - n
                            if vote > 0:                                
                                self._bot.say(c, 'The general public (%d) has agreed to kickban %s for %s' % (p + n, kb_users, options.timeout if kb_timeout else 'infinity'))
                                for u in options.arma:
                                    if self._bot.members(c).has_key(u) and self._bot.members(c)[u]:
                                        h = self._bot.members(c)[u].host
                                        self._bot.kickban(c, u, h, kb_reason)
                                        if kb_timeout:
                                            self._timer.register(options.timeout, self._bot.unban, (c, h,))
                            elif vote < 0:
                                self._bot.say(c, 'The general public (%d) has disagreed to kickban %s' % (p + n, kb_users))
                            else:
                                self._bot.say(c, 'The outcome is a draw! %s is/are saved.' % kb_users)
                        else:
                            self._bot.say(c, 'A minimum of 2 votes are required for taking decision.')
                    # Call
                    self._vote.start(channel, options.interval, 'kickban %s? (%s)' % (kb_users, kb_reason), self._bot.say, vote_result)    
                except Timer.SimpleError, e:
                    self._bot.notice(user.nick, 'Error: %s' % e.message)
        else:                                       # Regular vote
            args = ' '.join(options.args)
            def vote_result(c, p, n, q):
                vote = p - n
                if vote:
                    self._bot.say(c, 'The general public (%d) %s : %s' % ((p + n), 'agrees' if vote > 0 else 'disagrees', q))
                else:
                    self._bot.say(c, 'The outcome is a draw! Bummer.')
            self._vote.start(channel, options.interval, args, self._bot.say, vote_result)
        
    def is_voting(self, channel):
        return self._vote.is_voting(channel)
    
    def register_vote(self, channel, nick, host, vote):
        self._vote.register_vote(channel, nick, host, vote)
        
class RollModule(BaseDynamicExtension):
    '''
        Extension for performing word operations
    '''
    def build_meta(self, metadata):
        metadata.key = "roll"
        metadata.aliases = ["roll"]
        metadata.prefixes = ["!"]
        metadata.desc = "Roll a dice"
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!roll")
        parser.add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        parser.add_argument("-m", "--min", type=int, dest="min", default=1, help="Minimum range. Default %(default)s", metavar="M")
        parser.add_argument("-n", "--max", type=int, dest="max", default=6, help="Maximum range. Default %(default)s", metavar="N")
        return parser
        
    def reload(self):
        reload(Roll)
        
    def output(self, channel, user, options):              
        if options.min > 0 and options.max > 0 and options.min < options.max:
            r = Roll.roll(options.min, options.max)
        else:
            self._bot.notice(user.nick, 'Roll limits are weird, mate')
            r = None
        if r:
            if options.private:
                self._bot.notice(user.nick, r)
            else:
                return ModuleResult('%s rolled a %s' % (user.nick, r))   
            
class TwitterModule(BaseDynamicExtension):
    '''
        Module for sending message to twitter via IRC
    '''
    def build_meta(self, metadata):
        metadata.key = 'twitter'
        metadata.aliases = ['tweet', 't']
        metadata.prefixes = ['!']
        metadata.desc = 'Use twitter via an authenticated account'

    def build_parser(self):
        parser = SimpleArgumentParser(prog='!tweet')
        parser.add_argument("status", nargs="+", help="Status to tweet")
        return parser

    def reload(self):
        reload(Twitter)

    def output(self, channel, user, options):
        if len(options.status) == 1 and options.status[0] == '{{topic}}':
            status = self._bot.topic(channel)
            if status is None:
                return ModuleResult('%s, channel has no topic set' % user.nick)
            else:
                status = '%s : %s, set by %s on %s' % (channel, status['text'], status['user'], datetime.fromtimestamp(float(status['time'])).strftime('%b %d %Y %H:%M'))
        else:
            status = '<%s> %s' % (user.nick, ' '.join(options.status))
        
        r = Twitter.tweet(status)
        return ModuleResult('%s, %s' % (r, user.nick)) 
        
        
class GameModule(BaseDynamicExtension):
    '''
        Extension for performing word operations
    '''
    def __init__(self, bot_state):
        super(GameModule, self).__init__(bot_state)
        self._werewolf = Game.Werewolf(callback=self._bot.say, pm=self._bot.notice)       
    
    def build_meta(self, metadata):
        metadata.key = "game"
        metadata.aliases = ["game"]
        metadata.prefixes = ["!"]
        metadata.desc = "Start a game"
        metadata.listeners = ["msg"]

    def event(self, key, channel, user, args):
        if key == "msg":            
            if self.is_joining(channel):
                if args == "+":
                    self.join(channel, user.nick)
                    return True
            elif self.is_playing(channel):
                self.response(channel, user.nick, args)            
                return True    
         
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!game")
        parser.add_argument("args", choices=["werewolf"], help="Name of the game")
        return parser
        
    def reload(self):
        reload(Game)
        
    def output(self, channel, user, options):              
        args = ' '.join(options.args)
        if args == 'werewolf':
            self._werewolf.start(channel)
            #r = 'Game is currently offline'       
        
    def is_joining(self, channel):
        return self._werewolf.is_joining(channel)
        
    def is_playing(self, channel):
        return self._werewolf.is_playing(channel)
    
    def is_running(self, channel):
        return self._werewolf.is_running(channel)
    
    def join(self, channel, nick):
        self._werewolf.join(channel, nick) 
        
    def response(self, channel, nick, msg):
        m = re.search(r'\+ ?([\S]*)', msg)
        if m:
            self._werewolf.lynch(channel, nick, m.group(1))
       
class CleverModule(BaseDynamicExtension):
    '''
        Extension for performing word operations
    '''
    def __init__(self, bot_state):
        super(CleverModule, self).__init__(bot_state)
        self._intelli = AI.PseudoIntelligence()    # AI module, Work in development
        self._cb = AI.CleverBot({'name': self._bot.nick})
        self.build_matcher()
                    
    def build_meta(self, metadata):
        metadata.key = "cleverbot"
        metadata.listeners = ["msg", "action", "nick"]
        
    def event(self, key, channel, user, args):        
        if key == "msg" or key == "action":            
            m = self._regex_query.match(args)
            if m and self.is_enabled():
                self.reply(channel, user, m.group(1)) 
        elif key == "nick":
            self.build_matcher()
            
    def build_matcher(self):
        self._regex_query = re.compile(r'^%s[\s,:]+(.+)$' % self._bot.nick)
        self._regex_verb = re.compile(r'^\s*([\S]+)(?:\s+([\S]+))(?:\s+(.*))?')
        
    def reload(self):
        reload(AI)
        
    def reply(self, channel, user, query):                    
        self.parse_verb(channel, query) or self.parse_pseudo(channel, query, user.nick) or self.parse_cleverbot(channel, query)
    
    def parse_pseudo(self, channel, query, nick):
        reply = self._intelli.reply(query, nick)
        if reply:
            self._bot.say(channel, reply)                                        
            return True
        else:
            return False
        
    def parse_cleverbot(self, channel, query):
        reply = self._cb.ask(query)
        if reply:                                                                         
            reply = htmlx.unescape(reply)
            self._bot.say(channel, reply)
            return True
        else:
            return False
        
    def parse_verb(self, channel, query):
        m = self._regex_verb.search(query)
        if m:
            return self._verb(channel, m.group(1), m.group(2), m.group(3))
            
    def _verb(self, channel, verb, nick, text):
        '''
            @param verb: The action text
            @param nick: The nick part
            @param text: The text message
            @summary: Parses verbs to present action for the bot 
        '''       
        if verb in ['dodge', 'give', 'steal', 'take', 'catch', 'arm', 'engage', 'assault', 'launch', 'slit', 'poke', 'strip', 'disarm', 'fire', 'attack', 'chase', 'create', 'make', 'relieve', 'show', 'escort', 'push', 'pull', 'throw', 'feed', 'fuck', 'sell', 'buy', 'oblige', 'demolish', 'destroy']:
            verb += 'es' if verb.endswith(('s', 'z', 'x', 'sh', 'ch'), -2) else 's'            
            if nick is not None:
                if text is None:
                    text = ''
                self._bot.action(channel, '%s %s %s' % (verb, nick, text))                
        elif verb == 'slap':
            self._bot.action(channel, 'bitchslaps %s' % (nick))       
        else:
            return False 
        return True 