'''
Created on Sep 18, 2012

@author: Nisheeth
'''
from Module import BaseExternalModule, ModuleResult
from Util.SimpleArgumentParser import SimpleArgumentParser
from Util import htmlx
import re
import time, datetime

class TimeModule(BaseExternalModule):
    '''
        Module for performing searches
    '''
            
    def build_trigger(self):
        return ('now', None)
            
    def build_parser(self):
        parser = SimpleArgumentParser(prog="!now")
        parser.add_argument("-p", "--private", action="store_true", dest="private", default=False, help="Get results in private")
        group = parser.add_mutually_exclusive_group()        
        group.add_argument("-u", "--utc", action="store_true", dest="utc", help="Get UTC time")
        group.add_argument("-t", "--timestamp", action="store_true", dest="timestamp", help="Get UNIX timestamp")
        parser.add_argument("int_timestamp", default=0, nargs="?", type=int, help="Decode a UNIX timestamp", metavar="TIMESTAMP")
        return parser
        
    def output(self, nick, host, auth, powers, options):
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
            if options.timestamp:                
                r = datetime.datetime.utcnow().replace(tzinfo=TZ_UTC()).strftime('%a, %d %b %Y %H:%M:%S %z')
        else:          
            if options.timestamp:
                r = int(time.mktime(datetime.datetime.now().timetuple()))
            else:            
                r = datetime.datetime.now(TZ_IST()).strftime('%a, %d %b %Y %H:%M:%S %z')
        if r:
            if options.private:
                self._bot.notice(nick, r)
            else:
                return ModuleResult('%s, %s' % (r, nick))   