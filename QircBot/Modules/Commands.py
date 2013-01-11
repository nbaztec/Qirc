'''
Created on Aug 5, 2012

@author: Nisheeth
'''

import re
from QircBot.Interfaces.BotInterface import CompleteInterface
from Util.Log import Log
from Module import BaseDynamicCommand
from Util.SimpleArgumentParser import SimpleArgumentParser
from Extensions import Enforce
from datetime import datetime
import os, gc, sys

#from meliae import scanner
#import psutil


class MemDumpCommandModule(BaseDynamicCommand):
    '''
        Extension for displaying help
    '''
    def build_meta(self, metadata):
        metadata.key = "memdump"
        metadata.aliases = ["memdump"]
        metadata.desc = "Memory Dump"    
    
    def build_parser(self):
        return SimpleArgumentParser(prog="memdump")
        
    def output(self, channel, user, options):
        #scanner.dump_all_objects("memory_dump")
        with open("memory_dump", "w") as f:            
            #f.write('%s\n' % psutil.Process(os.getpid()).get_memory_info())
            for obj in gc.get_objects():
                i = id(obj)
                size = sys.getsizeof(obj, 0)
                #    referrers = [id(o) for o in gc.get_referrers(obj) if hasattr(o, '__class__')]
                referents = [id(o) for o in gc.get_referents(obj) if hasattr(o, '__class__')]
                if hasattr(obj, '__class__'):
                    cls = str(obj.__class__)
                    f.write('%s\n' % {'id': i, 'class': cls, 'size': size, 'referents': referents})
       
class HelpCommandModule(BaseDynamicCommand):
    '''
        Extension for displaying help
    '''
    def build_meta(self, metadata):
        metadata.key = "help"
        metadata.aliases = ["help"]
        metadata.desc = "Show this help"    
    
    def build_parser(self):
        parser = SimpleArgumentParser(prog="help")
        parser.add_argument("-v", "--version", dest="version", action="store_true", help="List the version of the bot")
        return parser
        
    def output(self, channel, user, options):
        if options.version:
            from QircBot import __version__, __codename__
            self._bot.notice(user.nick, 'Qirc, %s [%s]' % (__version__, __codename__))
        else:
            max_len = 1
            l = []
            if user.powers is None:
                for _, v in self._bot.modules(1):
                    if len(v.aliases):
                        p = ''.join(v.prefixes)
                        if len(p) > 1:
                            p = '[%s]' % p
                        p = '%s%s' % (p, (', '+p).join(v.aliases))
                        if len(p) > max_len:
                            max_len = len(p)
                        l.append((p, v.desc))
            else:
                for pkey in user.powers:                
                    v = self._bot.module(pkey, 1)
                    if v and len(v.aliases):                    
                        p = ', '.join(v.aliases)
                        if len(p) > max_len:
                            max_len = len(p)
                        l.append((p, v.desc))
            s = ''
            for m in l:
                s += ('%-' + str(max_len+2) + 's%s\n') % m
            self._bot.send_multiline(self._bot.notice, user.nick, s.rstrip())
        

class PersistentJoinModule(BaseDynamicCommand):
    '''
        Module for persistent joining
    '''
    def build_meta(self, metadata):
        metadata.key = "pjoin"
        metadata.aliases = ["pjoin"]
        metadata.desc = "Add/Remove a channel from persitent joins"
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="pjoin")
        parser.add_argument("channels", nargs="*", help="Channel members", metavar="CHANNEL")
        parser.add_argument("-l", "--list", dest="list", action="store_true", default=True, help="List channel(s) to persitent join")
        parser.add_argument("-a", "--add", dest="add", action="store_true", help="Add channel(s) to persitent join")
        parser.add_argument("-r", "--remove", dest="remove", action="store_true", help="Remove channel(s) to persitent join")
        return parser
    
    def output(self, channel, user, options):        
        if options.add:
            for chan in options.channels:
                self._bot.add_retry_channel(chan)
            self._bot.notice(user.nick, '%d channel(s) have been added' % len(options.channels))
        elif options.remove:
            c = 0
            for chan in options.channels:
                if self._bot.remove_retry_channel(chan):
                    c += 1
            self._bot.notice(user.nick, '%d channel(s) have been removed' % c)
        else:
            self._bot.notice(user.nick, 'Retry Channels: %s' % ', '.join(self._bot.retry_channels()))
                   
class JoinModule(BaseDynamicCommand):
    '''
        Module for joining
    '''
    def build_meta(self, metadata):
        metadata.key = "join"
        metadata.aliases = ["join"]
        metadata.desc = "Join a channel"
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="join")
        parser.add_argument("chan", help="Join a channel", metavar="CHANNEL")
        parser.add_argument("key", nargs="?", default='', help="Channel key", metavar="KEY")
        return parser
    
    def output(self, channel, user, options):        
        self._bot.join(options.chan, options.key)        
        
class PartModule(BaseDynamicCommand):
    '''
        Module for joining
    '''
    
    def build_meta(self, metadata):
        metadata.key = "part"
        metadata.aliases = ["part"]
        metadata.desc = "Part from a channel"
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="part")
        parser.add_argument("chan", help="Part a channel", metavar="CHANNEL")
        parser.add_argument("msg", nargs="*", help="Part message", metavar="MESSAGE")
        return parser
    
    def output(self, channel, user, options):
        self._bot.part(options.chan, ' '.join(options.msg))
        
class QuitModule(BaseDynamicCommand):
    '''
        Module for managing quits
    '''    
    def build_meta(self, metadata):
        metadata.key = "quit"
        metadata.aliases = ["quit"]
        metadata.desc = "Quit IRC"
        metadata.interface = CompleteInterface
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="quit")
        parser.add_argument("-r", "--restart", action="store_true", dest="restart", default=False, help="Restart bot")
        parser.add_argument("msg", nargs="*", help="Quit message", metavar="MESSAGE")
        return parser
    
    def output(self, channel, user, options):
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
        
class KickModule(BaseDynamicCommand):
    '''
        Module for kicking
    '''
    
    def build_meta(self, metadata):
        metadata.key = "kick"
        metadata.aliases = ["kick"]
        metadata.desc = "Perform kicks"
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="kick")
        parser.add_argument("-r", "--reason", dest="reason", help="Kick reason")
        parser.add_argument("-c", "--channel", dest="chan", help="Channel", metavar="CHANNEL")
        parser.add_argument("nicks", nargs="+", help="Nicks of users", metavar="NICKS")
        return parser
    
    def output(self, channel, user, options):        
        if user.mgr_channel is None or options.chan in user.mgr_channel:
            if self._bot.has_status('kick'):
                if options.chan is None:
                    options.chan = self._bot.get_user_channel(user.nick)
                for nick in options.nicks:                    
                    self._bot.kick(options.chan, nick, options.reason)
        
class BanModule(BaseDynamicCommand):
    '''
        Module for managing bans
    '''
    
    def build_meta(self, metadata):
        metadata.key = "ban"
        metadata.aliases = ["ban"]
        metadata.desc = "Manage bans"
    
    def build_parser(self):
        parser = SimpleArgumentParser(prog="ban")
        parser.add_argument("-r", "--remove", action="store_true", help="Remove ban")
        parser.add_argument("-c", "--channel", dest="chan", help="Channel", metavar="CHANNEL")
        parser.add_argument("nicks", nargs="+", help="Nicks of users", metavar="NICKS")
        return parser
    
    def output(self, channel, user, options):
        if user.mgr_channel is None or options.chan in user.mgr_channel:
            if self._bot.has_status('ban'):
                if options.chan is None:
                    options.chan = self._bot.get_user_channel(user.nick)
                if options.remove:                
                    for nick in options.nicks:
                        self._bot.unban(options.chan, nick)
                else:
                    for nick in options.nicks:
                        self._bot.ban(options.chan, nick)
        
class OpModule(BaseDynamicCommand):
    '''
        Module for performing OPs and DEOPs
    '''
    
    def build_meta(self, metadata):
        metadata.key = "op"
        metadata.aliases = ["op"]
        metadata.desc = "Perform OP/DEOP on users"
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="op")
        parser.add_argument("-r", "--remove", dest="remove", action="store_true", default=False, help="Deop user")
        parser.add_argument("chan", help="Channel", metavar="CHANNEL")
        parser.add_argument("nick", nargs="?", help="Nicks of users", metavar="NICK")
        return parser
    
    def output(self, channel, user, options):        
        if user.mgr_channel is None or options.chan in user.mgr_channel:
            if options.nick is None:
                options.nick = self._bot.nick                            
            
            if options.chan is None:
                options.chan = self._bot.get_user_channel(user.nick)
                    
            if options.remove:
                self._bot.deop(options.chan, options.nick)
            else:
                self._bot.op(options.chan, options.nick) 
        
class SayModule(BaseDynamicCommand):
    '''
        Module for performing say operations
    '''
    
    def build_meta(self, metadata):
        metadata.key = "say"
        metadata.aliases = ["say"]
        metadata.desc = "Say something to nick/channel"
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="say")
        parser.add_argument("-w", "--whisper", dest="notice", help="Whisper to user", metavar="NICK")
        parser.add_argument("-s", "--self", dest="me", action="store_true", help="Speak to self")
        parser.add_argument("-m", "--privmsg", dest="privmsg", help="Message to user", metavar="NICK")
        parser.add_argument("-c", "--channel", dest="chan", help="Say to channel", metavar="CHANNEL")
        parser.add_argument("msg", nargs="+", help="Message", metavar="MESSAGE")
        return parser
    
    def output(self, channel, user, options):
        options.msg = ' '.join(options.msg)
        if options.notice:
            self._bot.notice(options.notice, options.msg)
        elif options.me:
            self._bot.action(options.msg)
        elif options.privmsg:
            self._bot.msg(options.privmsg, options.msg)
        else:
            if options.chan is None:
                options.chan = self._bot.get_user_channel(user.nick)
            self._bot.say(options.chan, options.msg)    
        
class ArmageddonModule(BaseDynamicCommand):
    '''
        Module for handling armageddon
    '''
    def __init__(self, bot_state, whitelist=None):       
        BaseDynamicCommand.__init__(self, bot_state)
        if whitelist is None:
            whitelist = []
                    
        self._whitelist = whitelist
        self._resetlist = {}
        self._armadict = {}
        self._nicklist = {}
        self._state = -1
        self._recover = False
             
    def build_meta(self, metadata):
        metadata.key = "armageddon"
        metadata.aliases = ["armageddon"]
        metadata.desc = "Bring forth armageddon"
        metadata.listeners = ["mode", "userlist", "botpart"]
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="armageddon", prefix_chars="+-")
        parser.add_argument("-c", "--channel", dest="chan", help="Channel", metavar="CHANNEL")
        parser.add_argument("-u", "--users", nargs="*", dest="users", help="Selective users to arma", metavar="NICK")
        parser.add_argument("-r", "--recover", dest="recover", action="store_true", default=False, help="Unban all users banned in last armageddon")        
        parser.add_flag("+w", "-w", dest="whitelist", help="Add/Remove to/from whitelist")        
        parser.add_argument("-l", "--whitelist", dest="list", action="store_true", help="Display users on whitelist ")
        parser.add_argument("hostmasks", nargs="*", help="Hostname regex(+w) or indexes(+w, -w)", metavar="HOSTMASK|INDEX")
        return parser
    
    def event(self, key, channel, user, args):
        if key == "userlist":
            if self._state == 1:
                self._armadict[channel] = {}
                if self._nicklist[channel] is None:                    
                    self._armadict[channel] = self._bot.members(channel).copy()
                else:
                    for nick in self._nicklist[channel]:
                        if self._bot.members(channel).has_key(nick):
                            self._armadict[channel][nick] = self._bot.members(channel)[nick]
                self.armageddon(channel, 1)
            
        elif key == "mode":            
            if self._state == 2 and self._bot.nick in args[2] and self._bot.has_flag(channel, 'o'):
                self.armageddon(channel, 2)
            elif self._recover:
                self.arma_recover(channel)
        elif key == "botpart":
            if self._armadict.has_key(channel):
                self._armadict.pop(channel)
            if self._nicklist.has_key(channel):
                self._nicklist.pop(channel)
            if self._resetlist.has_key(channel):
                self._resetlist.pop(channel)
    
    def reset(self):
        self._nicklist = {}
        self._armadict = {}
        self._state = -1
            
    def armageddon(self, channel, stage=0, nicks=None):  
        '''
            @param build: True if called for first time, from stage 0. False otherwise.
            @summary: Does what it says. Armageddon.
                      Kickbans all users except the ones in whitelist
        ''' 
        self._state = stage + 1
        if stage == 0:                         # Stage 1, Prepare usernames
            self._nicklist[channel] = nicks
            self._bot.request_memberlist(channel)
        elif stage == 1:                       # Stage 2, Prepare userhosts
            if self._armadict[channel].has_key(self._bot.nick):
                self._armadict[channel].pop(self._bot.nick)      # Remove bot's nick from the list
            if len(self._armadict[channel]):                                
                self._bot.op(channel, self._bot.nick)
            else:
                self.reset()
        elif stage == 2:                                           # Final Stage, kickban everyone except in whitelist
            self._resetlist[channel] = []
            regx = None
            if len(self._whitelist):
                regx = re.compile(r'^%s' % '|'.join(self._whitelist)) # Set whitelist
            #regx = re.compile('|'.join(self._whitelist())) # Set whitelist
            for u in self._armadict[channel].values():
                if regx is None or regx.match(u.host) is None:                                        
                    Log.write('armageddon-kickban : %s : %s %s' % (channel, u.nick, u.host))
                    self._resetlist[channel].append('*!*@' + u.host)
                    self._bot.ban(channel, '*!*@' + u.host, False)                    
                    self._bot.kick(channel, u.nick, 'ARMAGEDDON', False)    
                else:
                    Log.write('Saved %s %s' % (u.nick, u.host))
                        
            # Reset vars
            self._bot.deop(channel, self._bot.nick)
            self._bot.flag(channel, 'o', False)
            self.reset()
    
    def arma(self, channel, usernames):
        '''
            @param usernames: The list of users to bring forth armageddon upon
            @summary: A toned down version of armageddon kickbanning only selected users 
        '''
        self.armageddon(channel, 0, usernames)
    
    def arma_recover(self, channel, auto_op=True):
        '''
            @param auto_op: If set to true ensures that the bot is +o'd first
            @summary: Recovers from the armageddon by unbanning all the people previously banned
        '''
        if self._resetlist.has_key(channel) and len(self._resetlist[channel]):
            if self._bot.has_flag(channel, 'o'):
                self._recover = False
                for u in self._resetlist[channel]:
                    Log.write('Unban %s' % u, 'D')
                    self._bot.unban(channel, u, False)
                self._bot.deop(channel, self._bot.nick)
                self._bot.flag(channel, 'o', False)
            elif auto_op:
                self._recover = True
                self._bot.op(channel, self._bot.nick)
            
    def output(self, channel, user, options):
        if options.whitelist is not None:            
            if options.whitelist:
                count = 0
                for hostmask in options.hostmasks:
                    if hostmask not in self._whitelist:
                        self._whitelist.append(hostmask)
                        count += 1
                self._bot.notice(user.nick, '%d hostmask(s) added' % count)
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
                self._bot.notice(user.nick, '%d hostmask(s) removed' % count)
                    
        elif options.list:
            self._bot.send_multiline(self._bot.notice, user.nick, 'Whitelisted hostnames are:\n' + '\n'.join([ '%2d) %s' % (i[0], i[1]) for i in zip(range(1,len(self._whitelist)+1), self._whitelist)]))
        else:
            if options.recover:
                if options.chan is None:
                    options.chan = self._bot.get_user_channel(user.nick)
                self.arma_recover(options.chan)
            elif options.users:
                if options.chan is None:
                    options.chan = self._bot.get_user_channel(user.nick)
                self.arma(options.chan, options.users)
            else:                    
                if options.chan:
                    self.armageddon(options.chan, 0)
                    self._bot.notice(user.nick, 'Commencing Armageddon!')
                else:
                    self._bot.notice(user.nick, 'Please specify a channel with -c/--c')
    
    def whitelist(self):
        return self._whitelist
    
    def get_state(self):
        d = super(self.__class__, self).get_state()        
        d.update({ 
                  'whitelist': self._whitelist,
                  'resetlist': self._resetlist 
                  })
        return d
    
    def set_state(self, state):
        self._whitelist = state['whitelist']
        self._resetlist = state['resetlist']
        super(self.__class__, self).set_state(state)
        
class FlagModule(BaseDynamicCommand):
    '''
        Module for handling flags
    '''
    
    def build_meta(self, metadata):
        metadata.key = "flags"
        metadata.aliases = ["flags"]
        metadata.desc = "Manage flags on bot"
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="flags", prefix_chars="+-", add_help=None, usage="flag [--desc] +/-[hukbv]")
        parser.add_help_argument("--desc", action="store_true", dest="desc", default=False, help="Show this desc")
        parser.add_flag("+h", "-h", dest="hear", help="Hear commands")
        parser.add_flag("+v", "-v", dest="voice", help="Voice results")        
        parser.add_flag("+k", "-k", dest="kick", help="Allow kicking")
        parser.add_flag("+b", "-b", dest="ban", help="Allow banning")        
        parser.add_flag("+u", "-u", dest="url", help="Enable url titles")    
        return parser
    
    def output(self, channel, user, options):
        nothing = True
        if user.auth == 0 and options.hear is not None:
            self._bot.status('hear', options.hear)
            nothing = False
        if options.voice is not None:
            self._bot.status('voice', options.voice)
            nothing = False        
        if options.kick is not None:
            self._bot.status('kick', options.kick)
            nothing = False
        if options.ban is not None:
            self._bot.status('ban', options.ban)
            nothing = False        
        if options.url is not None:
            self._bot.status('url', options.url)
            nothing = False
            
        # Build Flag String
        status = ''
        for k,v in self._bot.status():
            if v:
                status += k[0]
                    
        if nothing:            
            if len(status):
                self._bot.notice(user.nick, 'Flags are: +' + ''.join(sorted(status)))
            else:                                  
                self._bot.notice(user.nick, 'No flag are set')
        else:
            self._bot.notice(user.nick, 'Flag(s) have been updated: ' + ''.join(sorted(status)))
        
    def get_state(self):
        d = super(self.__class__, self).get_state()        
        d.update({ 'flag': self._bot.status(flag_dict=True) })
        return d
    
    def set_state(self, state):
        self._bot.status(flag_dict=True, value=state['flag'])
        super(self.__class__, self).set_state(state)
            
class EnforceModule(BaseDynamicCommand):
    '''
        Module for enforcing rules
    '''
    def __init__(self, bot_state):       
        BaseDynamicCommand.__init__(self, bot_state)
        self._enforcer = Enforce.Enforcer() 
        self._regex_name = re.compile(r'^:([^!]+)!([^@]+)@(.*)$')
        
    def build_meta(self, metadata):
        metadata.key = "enforce"
        metadata.aliases = ["enforce"]
        metadata.desc = "Enforce kick/ban/kickban rules"
        metadata.listeners = ["join", "nick"]
        
    def event(self, key, channel, user, args):
        if key == "join":
            if user.nick != self._bot.nick:
                self.enforce(channel, user.nick, user.ident, user.host)
        elif key == "nick":
            if args != self._bot.nick:
                self.enforce(channel, args, user.ident, user.host)
            
    def build_parser(self):
        parser = SimpleArgumentParser(prog="enforce")        
        parser.add_argument("-a", "--add", dest="add", choices=["kick", "ban", "arma"], default="kick", help="Enforce a rule [Default: kick]", metavar="GROUP")
        parser.add_argument("-l", "--list", dest="list", action="store_true", help="List rules")
        parser.add_argument("-r", "--remove", dest="remove", choices=["kick", "ban", "arma"], help="Remove rule", metavar="GROUP")
        parser.add_argument("-x", "--regex", dest="regex", action="store_true", help="Rule is a regex")
        parser.add_argument("rule", nargs="*", help="Match rule (add), Group (list), Rule/Index (remove)", metavar="RULE|GROUP|INDEX")
        return parser
    
    def reload(self):
        reload(Enforce)
        
    def output(self, channel, user, options):
        if len(options.rule) == 0:
            if options.list:                
                if len(options.rule):
                    d = self._enforcer.rules(options.rule)
                    if d:
                        d = {options.rule: d}
                else:
                    d = self._enforcer.rules()
                    
                if d:
                    self._bot.send_multiline(self._bot.notice, user.nick, '\n'.join('Rules for "%s" are:\n%s' % (k, '\n'.join(['%s) %s %s' % (i[0], i[1][0], '[regex]' if i[1][1] else '') for i in zip(range(1, len(v)+1), v)])) for k, v in d.items()))
                else:
                    self._bot.notice(user.nick, 'No rules exist')
            else:
                self._bot.send_multiline(self._bot.notice, user.nick, self.desc())
        else:
            options.rule = ' '.join(options.rule)
            if options.remove:               
                if options.rule[0] == '%':
                    try:
                        if self._enforcer.remove_at(options.remove, int(options.rule.lstrip('%')) - 1):
                            self._bot.notice(user.nick, 'Rule has been removed from group "%s"' % options.remove)
                    except ValueError:
                        if self._enforcer.remove(options.remove, options.rule):
                            self._bot.notice(user.nick, 'Rule has been removed from group "%s"' % options.remove)    
                else:
                    if self._enforcer.remove(options.remove, options.rule, options.regex):
                        self._bot.notice(user.nick, 'Rule has been removed from group "%s"' % options.remove)                                    
            else:                                                                    
                if self._enforcer.add(options.add, options.rule, options.regex):                                       
                    self._bot.notice(user.nick, 'Rule has been enforced to a new group "%s"' % options.add)
                else:  
                    self._bot.notice(user.nick, 'Rule has been enforced to group "%s"' % options.add)
            
    def enforce(self, channel, nick, ident, host):
        action = self._enforcer.enforce('%s!%s@%s' % (nick, ident, host))
        #m = self._regex_name.match(':'+user)
        if action == "kick":  
            self._bot.kick(channel, nick, "The kinds of you aren't welcome here")
        elif action == "ban":
            self._bot.ban(channel, '*!*@'+host)
        elif action == "arma":
            self._bot.kickban(channel, nick, '*!*@'+host, "The kinds of you aren't welcome here")#self._regex_name.search(':'+nick).group(1)])
            
    def get_state(self):
        r = {'rules': {}}        
        for k, v in self._enforcer.rules().items():
            r['rules'][k] = []
            for rule in v:            
                r['rules'][k].append(rule)
        d = super(self.__class__, self).get_state()        
        d.update(r)        
        return d
    
    def set_state(self, state):                
        for k, v in state['rules'].items():
            for r, e in v:
                self._enforcer.add(k, r, e)
        super(self.__class__, self).set_state(state)
        
class UserAuthModule(BaseDynamicCommand):
    '''
        Handles the users of the bot
    '''
    
    def build_meta(self, metadata):
        metadata.key = "users"
        metadata.aliases = ["users"]
        metadata.desc = "Manage users of bot"
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="users")
        group = parser.add_mutually_exclusive_group()        
        group.add_argument("-a", "--add", dest="add", help="Add to this group", metavar="GROUP")        
        group.add_argument("-r", "--remove", dest="remove", help="Remove from this group", metavar="GROUP")        
        group.add_argument("-l", "--list", dest="list", action="store_true", help="List the users of a bot")
        parser.add_argument("-c", "--channel", dest="chan", help="Channel for 'chan_mgr' group member", metavar="CHANNEL")
        parser.add_argument("-t", "--auth", dest="auth", action="store_true", help="Authority level for group (0-255)")
        parser.add_argument("-p", "--power", dest="power", action="store_true", help="Specify the powers")
        parser.add_argument("hostmasks", nargs="*", help="User's hostmask or powers (-p) or auth (-t)", metavar="HOSTMASK|POWER|AUTH")
        return parser
    
    def output(self, channel, user, options):
        if options.add:
            if options.auth:                
                try:
                    a = int(options.hostmasks[0])
                    if a > self._bot.user_auth(user=user.host) and self._bot.role_add(options.add, a):                        
                        self._bot.notice(user.nick, 'The group "%s" has been added with authority level %d' % (options.add, a))
                    else:
                        self._bot.notice(user.nick, 'You can only add groups with lower auth than yours.')
                except ValueError:
                    self._bot.notice(user.nick, 'Invalid value for auth. Please use integers only.')
            elif self._bot.user_auth(role=options.add) > self._bot.user_auth(user=user.host):
                if options.power:
                    count = 0
                    for power in options.hostmasks:
                        if self._bot.role_power(options.add, power):
                            count += 1
                    self._bot.notice(user.nick, '%d power(s) added to group %s' % (count, options.add))                
                else:
                    count = 0
                    for hostmask in options.hostmasks:
                        if self._bot.user_add(options.add, hostmask, options.chan):
                            count += 1
                    self._bot.notice(user.nick, '%d hostmask(s) added as %s' % (count, options.add))
            else:                
                self._bot.notice(user.nick, 'You can only add users/powers to a lower group than yourself')
        elif options.list:
            if options.power:
                self._bot.send_multiline(self._bot.notice, user.nick, 'Powers are:\n' + '\n'.join(['[%s] : %s' % (k, ', '.join(['All'] if l is None else l)) for k, l in self._bot.power_list(sort=True)]))            
            elif options.auth:
                self._bot.send_multiline(self._bot.notice, user.nick, 'Roles are:\n' + '\n'.join(['[%s] : %s' % (k, l) for k, l in self._bot.role_list(sort=True)]))
            else:
                self._bot.send_multiline(self._bot.notice, user.nick, 'Users are:\n' + '\n'.join(['[%s] : %s' % (k, ', '.join(l)) for k, l in self._bot.user_list(sort=True)]))
        elif options.remove:            
            if self._bot.user_auth(role=options.remove) > self._bot.user_auth(user=user.host):
                if options.power:
                    count = 0
                    for power in options.hostmasks:                        
                        if self._bot.role_power(options.remove, power, remove=True):
                            count += 1
                    self._bot.notice(user.nick, '%d power(s) removed from group %s' % (count, options.remove))
                elif options.auth:
                    if self._bot.role_remove(options.remove):
                        self._bot.notice(user.nick, 'The group "%s" has been removed' % options.remove)
                else:
                    count = 0
                    for hostmask in options.hostmasks:
                        if self._bot.user_remove(options.remove, hostmask, options.chan):
                            count += 1
                    self._bot.notice(user.nick, '%d hostmask(s) removed from %s' % (count, options.remove))
            else:
                self._bot.notice(user.nick, 'You can only remove users/powers of a lower group than yourself')
                

class ModManagerModule(BaseDynamicCommand):
    '''
        Handles the module management of the bot
    '''
    
    def build_meta(self, metadata):
        metadata.key = "module"
        metadata.aliases = ["module"]
        metadata.desc = "Manage modules"
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="module")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-e", "--enable", dest="enable", action="store_true", help="Enable the module")
        group.add_argument("-d", "--disable", dest="disable", action="store_true", help="Disable the module")
        group.add_argument("-r", "--reload", dest="reload", action="store_true", help="Reload the module [Default: All]")
        
        parser.add_argument("-l", "--list", dest="list", action="store_true", help="List the modules [Default: All]")
        
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-f", "--config", dest="config", action="store_true", help="Configuration")
        group.add_argument("-i", "--internal", dest="internal", action="store_true", help="Internal module")
        group.add_argument("-x", "--external", dest="external", action="store_true", help="External module")
        group.add_argument("-c", "--command", dest="command", action="store_true", help="Command module")
        
        parser.add_argument("keys", nargs="*", help="Module Key", metavar="KEY")
        return parser
    
    def output(self, channel, user, options):
                
        mgr_type = 1 if options.command else 0        
         
        if options.list:
            s = ''
            if not options.command:
                s += '[Extensions]\n'
                if not options.disable:
                    s += 'Enabled: %s\n' % ', '.join(self._bot.module_keys(0, True))
                if not options.enable:
                    s += 'Disabled: %s\n' % ', '.join(self._bot.module_keys(0, False))
            if not (options.internal or options.external):    
                s += '[Commands]\n'
                if not options.disable:
                    s += 'Enabled: %s\n' % ', '.join(self._bot.module_keys(1, True))
                if not options.enable:
                    s += 'Disabled: %s\n' % ', '.join(self._bot.module_keys(1, False))                        
            self._bot.send_multiline(self._bot.notice, user.nick, s)       
        elif options.enable:
            for key in options.keys:
                if key != self.key:
                    module = self._bot.module(key, mgr_type)
                    if module is None:
                        self._bot.notice(user.nick, "No such module named '%s'" % key)
                    elif module.enable():
                        self._bot.notice(user.nick, "The module '%s' has been enabled" % key)
                    else:
                        self._bot.notice(user.nick, "Module '%s' state unchanged" % key)
        elif options.disable:
            for key in options.keys:
                if key != self.key:
                    module = self._bot.module(key, mgr_type)
                    if module is None:
                        self._bot.notice(user.nick, "No such module named '%s'" % key)  
                    elif module.disable():
                        self._bot.notice(user.nick, "The module '%s' has been disabled" % key)
                    else:
                        self._bot.notice(user.nick, "Module '%s' state unchanged" % key)
        elif options.reload:
            self._bot.save_state()
            if options.config:
                self._bot.reload_config()
                self._bot.notice(user.nick, 'Bot configuration has been reloaded')
            elif options.internal:
                if len(options.keys):
                    c = 0
                    for key in options.keys:                    
                        if self._bot.reload_extensions(key, 1):
                            c += 1
                    self._bot.notice(user.nick, '%d internal extension(s) have been reloaded' % c)
                else:
                    self._bot.reload_extensions(None, 1)
                    self._bot.notice(user.nick, 'All internal extensions have been reloaded')
            elif options.external:
                if len(options.keys):
                    c = 0
                    for key in options.keys:                    
                        if self._bot.reload_extensions(key, 2):
                            c += 1
                    self._bot.notice(user.nick, '%d external extension(s) have been reloaded' % c)
                else:
                    self._bot.reload_extensions(None, 2)
                    self._bot.notice(user.nick, 'All external extensions have been reloaded')
            elif options.command:
                if len(options.keys):
                    c = 0
                    for key in options.keys:                    
                        if self._bot.reload_commands(key):
                            c += 1
                    self._bot.notice(user.nick, '%d command(s) have been reloaded' % c)
                else:
                    self._bot.reload_commands()
                    self._bot.notice(user.nick, 'All commands have been reloaded')
            else:
                self._bot.reload_extensions(None, 0)
                self._bot.reload_commands()
                self._bot.notice(user.nick, 'All modules have been reloaded')
                
class SimpleLogModule(BaseDynamicCommand):
    '''
        Handles the logging task of the bot, logs are split on day
    '''
    def __init__(self, bot_state):
        super(SimpleLogModule, self).__init__(bot_state)
        #self._format = 'QircLog[%Y.%m.%d]'              # Log format
        #self._dir = 'logs-ignore/'                      # Log directory
        self._format = self._bot.config('logs', 'file-format')           # Log format
        self._dir = self._bot.config('logs', 'dir')                      # Log directory
        self._file = None
        self._buffer = ""
        self._bufferlen = self._bot.config('logs', 'buffer-len')
        self._date = datetime(1970, 1, 1)
        self._regex_name = re.compile(r'^:?([^!]+)!([^@]+)@(.*)$')
        self._regex_subst = re.compile(r'{(\w+)(:(?:[^}\\]|\\.)*)?}')        
            
    def build_meta(self, metadata):
        metadata.key = "log"        
        metadata.listeners = ["join", "nick", "mode", "msg", "action", "privmsg", "notice", "broadcast", "kick", "part", "quit", "botquit", "botpart", "exit", "topic"]#, "ping", "pong", "motd_end"]
        
    def event(self, key, channel, user, args):
        if key == "join":
            self.joined(user, channel)
        elif key == "nick":
            self.nick(user, channel, args)
        elif key == "mode":
            self.mode(user, channel, '%s%s' % (args[0], args[1]), args[2])
        elif key == "msg":
            self.msg(user, channel, args)
        elif key == "action":
            self.msg(user, channel, args, action=True)
        elif key == "privmsg":
            self.msg(user, channel, args)
        elif key == "notice":
            self.msg(user, channel, args, notice=True)
        elif key == "broadcast":
            self.msg(user, channel, args, broadcast=True)
        elif key == "kick":
            self.kicked(channel, user, args[0], args[1])
        elif key == "part" or key == "botpart":
            self.parted(user, channel, args)
        elif key == "quit":
            self.quit(user, channel, args)
        elif key == "botquit":
            self.quit(user, None, args)        
        elif key == "exit" or key == "reload":
            self.close()
        elif key == "topic":
            self.topic(user, channel, int(args[0]), args[1])
        elif key == "motd_end":
            self.log(None, "END MOTD")
        elif key == "ping":
            self.log(None, "PING: %s" % args)
        elif key == "pong":
            self.log(None, "PONG: %s [%s]" % (args[0], args[1]))    
            
    def parse_template(self, pattern, channel, timestamp):
        def regex_sub(match):            
            if match.group(1) == 'channel':
                if channel and channel.startswith('#'):
                    return channel.lstrip('#')
                else:
                    return 'PRIVATE'
            elif match.group(1) == 'timestamp':
                f = '%Y.%m.%d'
                if match.group(2):
                    f = match.group(2).lstrip(':')                
                return datetime.strftime(timestamp, f)
            else:
                return ''
        return self._regex_subst.sub(regex_sub, pattern)
        
    def close(self):
        if self._file:
            self._file.write(self._buffer)
            self._buffer = ""
            self._file.close()
            
    def log(self, channel, msg):
        if self.is_enabled():
            now = datetime.utcnow()            
            dirpath = self.parse_template(self._dir, channel, now)
            filename = os.path.join(dirpath , self.parse_template(self._format, channel, now))
            #d = now - self._date
            if self._date.date() != now.date() or (self._file and filename != self._file.name):
                self._date = now
                self.close()    
                if not os.path.exists(dirpath):
                    os.makedirs(dirpath)            
                self._file = open(filename, "a")
                Log.write('Opening Log: ' + self._file.name)
                        
            self._buffer += datetime.strftime(now, "[%H:%M:%S] ") + msg + '\n'
            if len(self._buffer) > self._bufferlen:
                self._file.write(self._buffer)
                self._file.flush()
                self._buffer = ""             
    
    def joined(self, user, channel):
        self.log(channel, "JOIN: %s joined %s" % (user, channel))
    
    def kicked(self, channel, user, source, reason):        
        self.log(channel, "KICK: %s was kicked by %s from %s. Reason: %s" % (user, source, channel, reason))
    
    def banned(self, user, channel):
        self.log(channel, "BAN: %s banned from %s" % (user, channel))
    
    def parted(self, user, channel, reason):
        self.log(channel, "PART: %s parted from %s. Reason: %s" % (user, channel, reason))
    
    def quit(self, user, channel, reason):
        self.log(channel, "QUIT: %s quit. Reason: %s" % (user, reason))
    
    def topic(self, user, channel, timestamp, topic):
        self.log(channel, "TOPIC: Set on %s by %s at %s | %s" % (channel, user, datetime.utcfromtimestamp(timestamp).strftime('%b %d, %Y %H:%M'), topic))
        
    def mode(self, source, channel, flags, users):
        if users:
            self.log(channel, "MODE: %s set mode %s for %s on %s" % (source, flags, ', '.join(users), channel))
        else:
            self.log(channel, "MODE: %s set mode %s on %s" % (source, flags, channel))
        
    def nick(self, user, channel, new_nick):
        self.log(channel, "NICK: %s is now known as %s" % (user, new_nick))
    
    def msg(self, user, channel, msg, notice=False, broadcast=False, action=False):        
        if action:
            self.log(channel, "ACTION: %s %s" % (user.nick, msg))
        else:
            if notice:                
                self.log(channel, "<%s whispers> %s" % (user.nick if user.nick else user, msg))
            elif broadcast:
                self.log(channel, "%s : %s" % (user.nick if user.nick else user, msg))
            elif channel:
                self.log(channel, "<%s> %s" % (user.nick, msg))
            else:
                self.log(None, "<%s> %s" % (user.nick, msg))    