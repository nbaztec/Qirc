'''
Created on Sep 18, 2012

@author: Nisheeth
'''
from QircBot.Interfaces.BotInterface import EnforcerInterface
from Module import BaseDynamicExtension, ModuleResult
from Util.SimpleArgumentParser import SimpleArgumentParser
from Extensions import Twipper

import re
import time, datetime

class ConvertWeightModule(BaseDynamicExtension):
    '''
        Module for performing simple KG-LB weight conversion
    '''
            
    def build_meta(self, metadata):
        metadata.key = "demo_weight"
        metadata.aliases = ["kglb"]
        metadata.prefixes = ["!."]
        metadata.desc = "Perform KG-LB conversions"
            
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!kglb")
        parser.add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")        
        parser.add_argument("-r", "--reverse", action="store_true", dest="reverse", help="Convert pounds to kilograms")
        parser.add_argument("weight", default=0, type=float, help="Convert weight to pounds/kilograms", metavar="WEIGHT")
        return parser
        
    def output(self, channel, user, options):        
        if options.reverse:
            r = '%.2f lb = %.2f kg' % (options.weight, options.weight * 0.453592)
        else:
            r = '%.2f kg = %.2f lb' % (options.weight, options.weight * 2.20462)
        
        if options.private:
            self._bot.notice(user.nick, r)
        else:
            return ModuleResult('%s, %s' % (r, user.nick))
                       
class LolModule(BaseDynamicExtension):
    '''
        Module for detecting 'lol' in a message
    '''
            
    def build_meta(self, metadata):
        metadata.key = "demo_lol"
        metadata.listeners = ["msg", "action"]            
        
    def event(self, key, channel, user, args):
        if (key == 'msg' or key == 'action') and self.is_enabled():
            if args.find('lol') != -1:
                self.bot.say(channel, "LAUGHING OUT LOUD!!!111112")
                
class HolyModule(BaseDynamicExtension):
    '''
        Module for checking swear words
    '''
            
    def build_meta(self, metadata):
        metadata.key = "demo_holy"
        metadata.listeners = ["msg", "action"]
        metadata.interface = EnforcerInterface        
        self.regex = re.compile(r'\b(fuck|asshole|(mother|sister)fucker)\b', re.I)
                    
    def event(self, key, channel, user, args):
        if (key == 'msg' or key == 'action') and self.is_enabled():
            if self.regex.search(args):
                self.bot.kick(channel, user.nick, "NO SWEARING")
                
class AntiVyomModule(BaseDynamicExtension):
    '''
        Module for babysitting Vyom
    '''
            
    def build_meta(self, metadata):
        metadata.key = "demo_vyomic"
        metadata.listeners = ["msg", "action"]
        metadata.interface = EnforcerInterface
                    
    def event(self, key, channel, user, args):
        if (key == 'msg' or key == 'action') and self.is_enabled():            
            if user.host == "unaffiliated/vy0m" and re.search(r'\bnvm\b', args, re.I):
                self.bot.kick(channel, user.nick, "NVM? U NO KURT COBAIN!")

class SubstModule(BaseDynamicExtension):
    '''
        Module for detecting s/<>/<>/ in a message
    '''
    
    def build_meta(self, metadata):
        metadata.key = "demo_subst"
        metadata.listeners = ["msg"]
        
        self._last5lines = []
        self._regex = re.compile(r'^s/([^/]+|\\/)/([^/]*|\\/)/([gi]{0,2})$')
        
    def event(self, key, channel, user, args):
        if key == 'msg' and self.is_enabled():
            m = self._regex.match(args)            
            if m:
                for nick, line in self._last5lines:
                    l, c = re.subn(m.group(1), m.group(2), line, 1 if m.group(3).find('g') == -1 else 0, re.I if m.group(3).find('i') != -1 else 0)
                    if c:
                        if nick == user.nick:
                            self.bot.say(channel, '%s meant "%s"' % (nick, l))
                        else:                        
                            self.bot.say(channel, '%s implies %s meant "%s"' % (user.nick, nick, l))
                        break
            else:
                self._last5lines.insert(0, (user.nick, args))
                while len(self._last5lines) > 5:
                    self._last5lines.pop()
                
class TimeModule(BaseDynamicExtension):
    '''
        Module for retrieving current/UTC time
    '''
            
    def build_meta(self, metadata):
        metadata.key = "demo_now"
        metadata.aliases = ["now"]
        metadata.prefixes = ["!"]
        metadata.desc = "Display current time"
            
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!now")
        parser.add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        group = parser.add_mutually_exclusive_group()        
        group.add_argument("-u", "--utc", action="store_true", dest="utc", help="Get UTC time")
        group.add_argument("-t", "--timestamp", action="store_true", dest="timestamp", help="Get UNIX timestamp")
        parser.add_argument("int_timestamp", default=0, nargs="?", type=int, help="Decode a UNIX timestamp", metavar="TIMESTAMP")
        return parser
        
    def output(self, channel, user, options):
        # Internal classes for timezones        
        class TZ_UTC(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(0)
            def tzname(self, dt):
                return "UTC"
            def dst(self, dt):
                return datetime.timedelta(0)
        
        class TZ_IST(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(hours=5, minutes=30)
            def tzname(self, dt):
                return "IST"
            def dst(self, dt):
                return datetime.timedelta(0)
          
        if options.int_timestamp > 0:
            if options.utc:
                dt = datetime.datetime.utcfromtimestamp(options.int_timestamp)
            else:
                dt = datetime.datetime.fromtimestamp(options.int_timestamp)
            r = dt.strftime('%a, %d %b %Y %H:%M:%S %z')
        elif options.utc:
            r = datetime.datetime.utcnow().replace(tzinfo=TZ_UTC()).strftime('%a, %d %b %Y %H:%M:%S %z')
        else:          
            if options.timestamp:
                r = int(time.mktime(datetime.datetime.now().timetuple()))
            else:            
                r = datetime.datetime.now(TZ_IST()).strftime('%a, %d %b %Y %H:%M:%S %z')
        if r:
            if options.private:
                self._bot.notice(user.nick, r)
            else:
                return ModuleResult('%s, %s' % (r, user.nick))

class TwipperSendModule(BaseDynamicExtension):
    '''
        Module for sending message to twitter via IRC.
    '''
    def build_meta(self, metadata):
        metadata.key = 'twipper'
        metadata.aliases = ['t']
        metadata.prefixes = ['!']
        metadata.desc = 'Sends twitter via the authenticated account'

    def build_parser(self):
        parser = SimpleArgumentParser(prog='!t')
        parser.add_argument("tweet", nargs="+", help="Tweet this")
        return parser

    def reload(self):
        reload(Twipper)

    def output(self, channel, user, options):
        tweet = ' '.join(options.tweet)
        r = Twipper.post('<%s> %s'%(user.nick, tweet))
        return ModuleResult('%s, %s' % (r, user.nick))