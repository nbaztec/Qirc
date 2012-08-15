'''
Created on Aug 5, 2012

@author: Nisheeth
'''

import re
from Util.Log import Log
from Module import BaseModule
from Util.SimpleArgumentParser import SimpleArgumentParser
from Extensions.Enforcer import Enforcer
from datetime import datetime
import os

class JoinModule(BaseModule):
    '''
        Module for joining
    '''
    
    def build_parser(self):
        parser = SimpleArgumentParser(prog="join")
        parser.add_argument("chan", help="Join a channel", metavar="CHANNEL")
        parser.add_argument("key", nargs="?", default='', help="Channel key", metavar="KEY")
        return parser
    
    def output(self, nick, host, auth, powers, options):
        self._bot.join(options.chan, options.key)        
        
class QuitModule(BaseModule):
    '''
        Module for managin quits
    '''
    
    def build_parser(self):
        parser = SimpleArgumentParser(prog="quit")
        parser.add_argument("-r", "--restart", action="store_true", dest="restart", default=False, help="Restart bot")
        parser.add_argument("msg", nargs="*", help="Quit message", metavar="MESSAGE")
        return parser
    
    def output(self, nick, host, auth, powers, options):
        try:
            if options.restart:
                self._bot.disconnect(' '.join(options.msg) if options.msg else 'Restarting')
            else:
                self._bot.close()                                            
                self._bot.disconnect(' '.join(options.msg) if options.msg else "I'll be back")
        except Exception:
            Log.error('QircBot.parse_cmd: ')
        finally:        
            Log.stop()        
            return False        
        
class KickModule(BaseModule):
    '''
        Module for kicking
    '''
    
    def build_parser(self):
        parser = SimpleArgumentParser(prog="kick")
        parser.add_argument("-r", "--reason", dest="reason", help="Kick reason")
        parser.add_argument("nicks", nargs="+", help="Nicks of users", metavar="NICKS")
        return parser
    
    def output(self, nick, host, auth, powers, options):
        if self._bot.status('kick'):
            for nick in options.nicks:
                self._bot.kick(nick, options.reason)
        
class BanModule(BaseModule):
    '''
        Module for managing bans
    '''
    
    def build_parser(self):
        parser = SimpleArgumentParser(prog="ban")
        parser.add_argument("-r", "--remove", dest="remove", help="Remove ban")        
        parser.add_argument("nicks", nargs="+", help="Nicks of users", metavar="NICKS")
        return parser
    
    def output(self, nick, host, auth, powers, options):
        if self._bot.status('ban'):
            if options.remove:                
                for nick in options.nicks:
                    self._bot.unban(nick)
            else:
                for nick in options.nicks:
                    self._bot.ban(nick)
        
class OpModule(BaseModule):
    '''
        Module for performing OPs and DEOPs
    '''
    
    def build_parser(self):
        parser = SimpleArgumentParser(prog="op")
        parser.add_argument("-r", "--remove", dest="remove", action="store_true", default=False, help="Deop user")
        parser.add_argument("chan", nargs="?", help="Channel", metavar="CHANNEL")
        parser.add_argument("nick", nargs="?", help="Nicks of users", metavar="NICK")
        return parser
    
    def output(self, nick, host, auth, powers, options):
        if options.nick is None:
            options.nick = options.chan
            options.chan = self._bot.channel
            
        if options.nick is None:
            options.nick = self._bot.botnick                            
        
        if options.remove:
            self._bot.deop(options.chan, options.nick)
        else:
            self._bot.op(options.chan, options.nick) 
        
class SayModule(BaseModule):
    '''
        Module for performing say operations
    '''
    
    def build_parser(self):
        parser = SimpleArgumentParser(prog="say")
        parser.add_argument("-w", "--whisper", dest="notice", help="Whisper to user", metavar="NICK")
        parser.add_argument("-s", "--self", dest="me", help="Speak to self")
        parser.add_argument("-m", "--privmsg", dest="privmsg", help="Message to channel or user", metavar="NICK")        
        parser.add_argument("msg", nargs="+", help="Message", metavar="MESSAGE")
        return parser
    
    def output(self, nick, host, auth, powers, options):
        options.msg = ' '.join(options.msg)
        if options.notice:
            self._bot.notice(options.notice, options.msg)
        elif options.me:
            self._bot.action(options.msg)
        elif options.privmsg:
            self._bot.msg(options.privmsg, options.msg)
        else:
            self._bot.say(options.msg)    
        
class ArmageddonModule(BaseModule):
    '''
        Module for handling armageddon
    '''
    def __init__(self, interface, whitelist=None):       
        BaseModule.__init__(self, interface)
        if whitelist is None:
            whitelist = []
        self._whitelist = whitelist
             
    def build_parser(self):
        parser = SimpleArgumentParser(prog="armageddon", prefix_chars="+-")
        parser.add_argument("-u", "--users", nargs="*", dest="users", help="Selective users to arma", metavar="NICK")
        parser.add_argument("-r", "--recover", dest="recover", action="store_true", default=False, help="Unban all users banned in last armageddon")
        parser.add_flag("+w", "-w", dest="whitelist", help="Add/Remove to/from whitelist")        
        parser.add_argument("-l", "--whitelist", dest="list", action="store_true", help="Display users on whitelist ")
        parser.add_argument("hostmasks", nargs="*", help="Hostname regex(+w) or indexes(+w, -w)", metavar="HOSTMASK|INDEX")
        return parser
    
    def output(self, nick, host, auth, powers, options):
        if options.whitelist is not None:            
            if options.whitelist:
                count = 0
                for hostmask in options.hostmasks:
                    if hostmask not in self._whitelist:
                        self._whitelist.append(hostmask)
                        count += 1
                self._bot.notice(nick, '%d hostmak(s) added' % count)
            else:
                count = 0
                for hostmask in options.hostmasks:                    
                    try:
                        if hostmask[0] == '%':
                            idx = int(hostmask.lstrip('%'))
                            i = 1
                            for h in self._whitelist:
                                if i == idx:                      
                                    self._whitelist.remove(h)
                                    count += 1
                                    break     
                                i += 1                       
                        elif hostmask in self._whitelist:
                            self._whitelist.remove(hostmask)
                            count += 1                                
                    except:
                        pass                    
                self._bot.notice(nick, '%d hostmak(s) removed' % count)
                    
        elif options.list:
            self._bot.send_multiline(self._bot.notice, nick, 'Whitelisted hostnames are:\n' + '\n'.join([ '%2d) %s' % (i[0], i[1]) for i in zip(range(1,len(self._whitelist)+1), self._whitelist)]))
        else:
            if self._bot.status('arma'):
                if options.recover:
                    self._bot.arma_recover()
                elif options.users:
                    self._bot.arma(options.users)
                else:
                    self._bot.armageddon(build=True)      
    
    def whitelist(self):
        return self._whitelist
    
    def get_state(self):
        return { 'whitelist': self._whitelist } 
    
    def set_state(self, state):
        self._whitelist = state['whitelist']
        
class FlagModule(BaseModule):
    '''
        Module for handling flags
    '''
    
    def build_parser(self):
        parser = SimpleArgumentParser(prog="flags", prefix_chars="+-", add_help=None, usage="flags [--help] +/-[hulkbatv]")
        parser.add_argument("--help", action="store_true", dest="help", default=False, help="Show this help")
        parser.add_flag("+h", "-h", dest="hear", help="Hear commands")
        parser.add_flag("+v", "-v", dest="voice", help="Voice results")
        parser.add_flag("+l", "-l", dest="log", help="Enable enabled")
        parser.add_flag("+k", "-k", dest="kick", help="Allow kicking")
        parser.add_flag("+b", "-b", dest="ban", help="Allow banning")
        parser.add_flag("+a", "-a", dest="arma", help="Allow armageddon (kickban)")
        parser.add_flag("+t", "-t", dest="talk", help="Allow talking")
        parser.add_flag("+u", "-u", dest="url", help="Enable url titles")    
        return parser
    
    def output(self, nick, host, auth, powers, options):
        nothing = True
        if auth == 0 and options.hear is not None:
            self._bot.status('hear', options.hear)
            nothing = False
        if options.voice is not None:
            self._bot.status('voice', options.voice)
            nothing = False
        if options.log is not None:
            self._bot.status('log', options.log)
            self._bot.logger.enabled(options.log)            
            nothing = False
        if options.kick is not None:
            self._bot.status('kick', options.kick)
            nothing = False
        if options.ban is not None:
            self._bot.status('ban', options.ban)
            nothing = False
        if options.arma is not None:
            self._bot.status('arma', options.arma)
            nothing = False
        if options.talk is not None:
            self._bot.status('talk', options.talk)
            nothing = False
        if options.url is not None:
            self._bot.status('url', options.url)
            nothing = False
            
        if nothing:
            status = ''
            for k,v in self._bot.status():
                if v:
                    status += k[0]
            if len(status):
                self._bot.notice(nick, 'Flags are: +' + ''.join(sorted(status)))
            else:                                  
                self._bot.notice(nick, 'No flags are set')
        
    def get_state(self):
        return {'flags': self._bot.status(flag_dict=True)}
    
    def set_state(self, state):
        self._bot.status(flag_dict=True, value=state['flags'])
            
class EnforceModule(BaseModule):
    '''
        Module for enforcing rules
    '''    
    def __init__(self, interface):       
        BaseModule.__init__(self, interface)
        self._enforcer = Enforcer() 
        self._regex_name = re.compile(r'^:([^!]+)!([^@]+)@(.*)$')
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="enforce")        
        parser.add_argument("-k", "--kick", dest="kick", action="store_true", help="Enforce a kick [Default]")
        parser.add_argument("-b", "--ban", dest="ban", action="store_true", help="Enforce a ban")
        parser.add_argument("-l", "--list", dest="list", action="store_true", help="List rules")
        parser.add_argument("-r", "--remove", dest="remove", action="store_true", help="Remove rule (specify rule or index)")
        parser.add_argument("-e", "--regex", dest="regex", action="store_true", help="Rule is a regex")
        parser.add_argument("rule", nargs="*", help="Match rule", metavar="RULE")
        return parser
    
    def output(self, nick, host, auth, powers, options):
        if len(options.rule) == 0:
            if options.list:
                lst = self._enforcer.get_rules()
                if len(lst):
                    self._bot.send_multiline(self._bot.notice, nick, 'Rules are:\n' + '\n'.join([ '%2d) %s' % (i[0], i[1]) for i in zip(range(1,len(lst)+1), lst)]))
                else:
                    self._bot.notice(nick, 'No rules exist')
            else:
                self.send_multiline(self._bot.notice, nick, self.help())
        else:
            if options.regex:
                options.rule = ' '.join(options.rule)
            else:
                options.rule = ' '.join(options.rule).replace("*", ".*").replace("?", ".")
                
            if options.remove:
                try:
                    if options.rule[0] == '%':                    
                        if self._enforcer.remove_at(int(options.rule.lstrip('%')) - 1):
                            self._bot.notice(nick, 'Rule has been removed')
                except ValueError:
                    if self._enforcer.remove(options.rule):
                        self._bot.notice(nick, 'Rule has been removed')                            
            else:                                                                    
                self.add_enforce(options)                                       
                self._bot.notice(nick, 'Rule has been enforced')  
    
    def add_enforce(self, options):
        def enforce_kick(nick):                            
            self._bot.kick(self._regex_name.search(':' + nick).group(1), "The kinds of you aren't welcome here")
        def enforce_ban(nick):
            self._bot.ban(nick)
        def enforce_arma(nick):
            self._bot.kickban([self._regex_name.search(':'+nick).group(1)])
                                        
        if options.kick and options.ban:                            
            self._enforcer.add(options.rule, enforce_arma, 'arma')                            
        elif options.ban:
            self._enforcer.add(options.rule, enforce_ban, 'ban')
        else:
            self._enforcer.add(options.rule, enforce_kick, 'kick')
            
    def enforce(self, user):
        self._enforcer.enforce(user)  
        
    def get_state(self):
        d = {'rules': []}
        for r, v in self._enforcer.get_items():            
            d['rules'].append((r, v[1]))        
        return d 
    
    # Dummy class for anonymous object instantiation
    class Object(object):
            pass
        
    def set_state(self, state):                
        for i in state['rules']:
            o = self.Object()
            o.rule = i[0]
            o.kick = o.ban = 'arma'
            if i[1] == 'kick':
                o.ban = False
            elif i[1] == 'ban':
                o.kick = False
            self.add_enforce(o)
        
class UserAuthModule(BaseModule):
    '''
        Handles the users of the bot
    '''
    def build_parser(self):
        parser = SimpleArgumentParser(prog="users")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-a", "--add", dest="add", choices=["admin", "mod", "mgr"], help="Add a user", metavar="GROUP")        
        group.add_argument("-r", "--remove", dest="remove", help="Remove a user from group (specify user or index)", metavar="GROUP")        
        group.add_argument("-l", "--list", dest="list", action="store_true", help="List the users of a bot")
        parser.add_argument("-p", "--power", dest="power", action="store_true", help="Specify the powers")
        parser.add_argument("hostmasks", nargs="*", help="User's hostmask or group's powers (-p)", metavar="HOSTMASK|POWER")
        return parser
    
    def output(self, nick, host, auth, powers, options):
        if options.add:            
            if self._bot.user_auth(role=options.add) > self._bot.user_auth(user=host):
                if options.power:
                    count = 0
                    for power in options.hostmasks:
                        if self._bot.role_power(options.add, power):
                            count += 1
                    self._bot.notice(nick, '%d power(s) added to group %s' % (count, options.add))
                else:
                    count = 0
                    for hostmask in options.hostmasks:
                        if self._bot.user_add(options.add, hostmask):
                            count += 1
                    self._bot.notice(nick, '%d hostmak(s) added as %s' % (count, options.add))
            else:                
                self._bot.notice(nick, 'You can only add users to a lower group than yourself')
        elif options.list:
            if options.power:
                self._bot.send_multiline(self._bot.notice, nick, 'Powers are:\n' + '\n'.join(['[%s] : %s' % (k, ', '.join(['All'] if l is None else l)) for k, l in self._bot.power_list()]))            
            else:
                self._bot.send_multiline(self._bot.notice, nick, 'Users are:\n' + '\n'.join(['[%s] : %s' % (k, ', '.join(l)) for k, l in self._bot.user_list()]))
        elif options.remove:            
            if self._bot.user_auth(role=options.remove) > self._bot.user_auth(user=host):
                if options.power:
                    count = 0
                    for power in options.hostmasks:                        
                        if self._bot.role_power(options.remove, power, remove=True):
                            count += 1
                    self._bot.notice(nick, '%d power(s) removed from group %s' % (count, options.remove))
                else:
                    count = 0
                    for hostmask in options.hostmasks:
                        if self._bot.user_remove(options.remove, hostmask):
                            count += 1
                    self._bot.notice(nick, '%d hostmak(s) removed from %s' % (count, options.remove))
            else:
                self._bot.notice(nick, 'You can only remove users of a lower group than yourself')
                

class ModManagerModule(BaseModule):
    '''
        Handles the module management of the bot
    '''
    def build_parser(self):
        parser = SimpleArgumentParser(prog="module")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-e", "--enable", dest="enable", help="Enable the module", metavar="MODULE")
        group.add_argument("-d", "--disable", dest="disable", help="Disable the module", metavar="MODULE")
        return parser
    
    def output(self, nick, host, auth, powers, options):
        if options.enable:
            self._bot.module(options.enable).enable()
            self._bot.notice(nick, 'The module has been enabled')
        elif options.disable:            
            self._bot.module(options.disable).disable()
            self._bot.notice(nick, 'The module has been disabled')
           
class SimpleLogModule(BaseModule):
    '''
        Handles the logging task of the bot, logs are split on day
    '''
    def __init__(self):
        self._logging = True
        self._format = 'QircLog[%Y.%m.%d]'              # Log format
        self._dir = 'logs-ignore/'                      # Log directory
        self._file = None
        self._buffer = ""
        self._date = datetime(1970, 1, 1)
        self._regex_name = re.compile(r'^:([^!]+)!([^@]+)@(.*)$')
        if not os.path.exists(self._dir):
            os.makedirs(self._dir)
        
    def enabled(self, value=None):
        if value is None:
            return self._logging
        else:
            self._logging = value
            
    def parse_name(self, user):
        return self._regex_name.match(user).groups()
    
    def build_parser(self):
        return SimpleArgumentParser()
    
    def output(self, nick, host, auth, powers, options):
        if options.enable:
            self._bot.module(options.enable).enable()
            self._bot.notice(nick, 'The module has been enabled')
        elif options.disable:            
            self._bot.module(options.disable).disable()
            self._bot.notice(nick, 'The module has been disabled')
            
    def close(self):
        if self._file:            
            self._file.write(self._buffer)
            self._buffer = ""
            self._file.close()
            
    def log(self, msg):  
        if self._logging:
            now = datetime.utcnow()            
            d = now - self._date
            if d.days >= 1:
                self._date = now
                self.close()
                Log.write('Opening Log: ' + os.path.join(self._dir, datetime.strftime(self._date, self._format)))
                self._file = open(os.path.join(self._dir, datetime.strftime(self._date, self._format)), "a")
                        
            self._buffer += datetime.strftime(now, "[%H:%M:%S] ") + msg + '\n'
            #print msg
            if len(self._buffer) == 1024:                
                self._file.write(self._buffer)
                self._buffer = ""             
    
    def joined(self, user, channel):
        self.log("JOIN: %s joined %s" % (user.lstrip(':'), channel))
    
    def kicked(self, source, user, channel, reason):        
        self.log("KICK: %s was kicked by %s from %s. Reason: %s" % (user.lstrip(':'), source, channel, reason))
    
    def banned(self, user, channel):
        self.log("BAN: %s banned from %s" % (user.lstrip(':'), channel))
    
    def parted(self, user, channel, reason):
        self.log("PART: %s parted from %s. Reason: %s" % (user.lstrip(':'), channel, reason))
    
    def quit(self, user, reason):
        self.log("QUIT: %s quit. Reason: %s" % (user.lstrip(':'), reason))
    
    def mode(self, source, channel, flags, users):
        if len(users):
            self.log("MODE: %s set mode %s on %s for %s" % (source.lstrip(':'), flags, users, channel))
        else:
            self.log("MODE: %s set mode %s on %s" % (source.lstrip(':'), flags, channel))
        
    def nick(self, user, new_nick):
        self.log("NICK: %s is now known as %s" % (user.lstrip(':'), new_nick))
    
    def msg(self, user, channel, msg):
        nick, _, _ = self.parse_name(user)
        if msg.startswith('\x01ACTION '):
            self.log("ACTION: %s %s" % (nick, ''.join(msg[len('\x01ACTION '):-1])))
        else:
            if channel:
                self.log("<%s : %s> %s" % (nick, channel, msg))
            else:
                self.log("<%s> %s" % (nick, msg))
                
    def get_state(self):
        return {'enabled': self._logging}
    
    def set_state(self, state):
        self._logging = state['enabled']
        

# Set the logging module        
LogModule = SimpleLogModule