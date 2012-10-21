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
import os

class JoinModule(BaseDynamicCommand):
    '''
        Module for joining
    '''
    def build_meta(self, metadata):
        metadata.key = "join"
        metadata.aliases = ["join"]
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="join")
        parser.add_argument("chan", help="Join a channel", metavar="CHANNEL")
        parser.add_argument("key", nargs="?", default='', help="Channel key", metavar="KEY")
        return parser
    
    def output(self, nick, host, auth, powers, options):
        self._bot.join(options.chan, options.key)        
        
class PartModule(BaseDynamicCommand):
    '''
        Module for joining
    '''
    
    def build_meta(self, metadata):
        metadata.key = "part"
        metadata.aliases = ["part"]
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="part")
        parser.add_argument("chan", help="Part a channel", metavar="CHANNEL")
        parser.add_argument("msg", nargs="*", help="Part message", metavar="MESSAGE")
        return parser
    
    def output(self, nick, host, auth, powers, options):
        self._bot.part(options.chan, ' '.join(options.msg))
        
class QuitModule(BaseDynamicCommand):
    '''
        Module for managin quits
    '''
    
    def build_meta(self, metadata):
        metadata.key = "quit"
        metadata.aliases = ["quit"]
        metadata.interface = CompleteInterface
        
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
        
class KickModule(BaseDynamicCommand):
    '''
        Module for kicking
    '''
    
    def build_meta(self, metadata):
        metadata.key = "kick"
        metadata.aliases = ["kick"]
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="kick")
        parser.add_argument("-r", "--reason", dest="reason", help="Kick reason")
        parser.add_argument("nicks", nargs="+", help="Nicks of users", metavar="NICKS")
        return parser
    
    def output(self, nick, host, auth, powers, options):
        if self._bot.has_status('kick'):
            for nick in options.nicks:
                self._bot.kick(nick, options.reason)
        
class BanModule(BaseDynamicCommand):
    '''
        Module for managing bans
    '''
    
    def build_meta(self, metadata):
        metadata.key = "ban"
        metadata.aliases = ["ban"]
    
    def build_parser(self):
        parser = SimpleArgumentParser(prog="ban")
        parser.add_argument("-r", "--remove", action="store_true", help="Remove ban")        
        parser.add_argument("nicks", nargs="+", help="Nicks of users", metavar="NICKS")
        return parser
    
    def output(self, nick, host, auth, powers, options):
        if self._bot.has_status('ban'):
            if options.remove:                
                for nick in options.nicks:
                    self._bot.unban(nick)
            else:
                for nick in options.nicks:
                    self._bot.ban(nick)
        
class OpModule(BaseDynamicCommand):
    '''
        Module for performing OPs and DEOPs
    '''
    
    def build_meta(self, metadata):
        metadata.key = "op"
        metadata.aliases = ["op"]
        
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
            options.nick = self._bot.nick                            
        
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
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="say")
        parser.add_argument("-w", "--whisper", dest="notice", help="Whisper to user", metavar="NICK")
        parser.add_argument("-s", "--self", dest="me", action="store_true", help="Speak to self")
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
        
class ArmageddonModule(BaseDynamicCommand):
    '''
        Module for handling armageddon
    '''
    def __init__(self, bot_state, whitelist=None):       
        BaseDynamicCommand.__init__(self, bot_state)
        if whitelist is None:
            whitelist = []
                    
        self._whitelist = whitelist
        self._resetlist = []
        self._state = -1
        self._recover = False
             
    def build_meta(self, metadata):
        metadata.key = "armageddon"
        metadata.aliases = ["armageddon"]
        metadata.listeners = ["mode", "userlist"]
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="armageddon", prefix_chars="+-")
        parser.add_argument("-u", "--users", nargs="*", dest="users", help="Selective users to arma", metavar="NICK")
        parser.add_argument("-r", "--recover", dest="recover", action="store_true", default=False, help="Unban all users banned in last armageddon")
        parser.add_flag("+w", "-w", dest="whitelist", help="Add/Remove to/from whitelist")        
        parser.add_argument("-l", "--whitelist", dest="list", action="store_true", help="Display users on whitelist ")
        parser.add_argument("hostmasks", nargs="*", help="Hostname regex(+w) or indexes(+w, -w)", metavar="HOSTMASK|INDEX")
        return parser
    
    def event(self, key, channel, user, args):
        if key == "userlist":
            if self._state == 1:
                self._armadict = {}
                if self._nicklist is None:                    
                    self._armadict = self._bot.names.copy()
                else:
                    for nick in self._nicklist:
                        if self._bot.names.has_key(nick):
                            self._armadict[nick] = self._bot.names[nick]
                self.armageddon(1)
            
        elif key == "mode":            
            if self._state == 2 and self._bot.nick in args[2] and self._bot.has_flag('o'):
                self.armageddon(2)
            elif self._recover:
                self.arma_recover()                
    
    def reset(self):
        self._nicklist = None
        self._armadict = None
        self._state = -1
            
    def armageddon(self, stage=0, nicks=None):  
        '''
            @param build: True if called for first time, from stage 0. False otherwise.
            @summary: Does what it says. Armageddon.
                      Kickbans all users except the ones in whitelist
        ''' 
        self._state = stage + 1
        if stage == 0:                         # Stage 1, Prepare usernames
            self._nicklist = nicks            
            self._bot.request_names()            
        elif stage == 1:                       # Stage 2, Prepare userhosts
            if self._armadict.has_key(self._bot.nick):
                self._armadict.pop(self._bot.nick)      # Remove bot's nick from the list
            if len(self._armadict):                                
                self._bot.op(self._bot.channel, self._bot.nick)
            else:
                self.reset()
        elif stage == 2:                                           # Final Stage, kickban everyone except in whitelist
            self._resetlist = []
            regx = re.compile(r'^%s' % '|'.join(self._whitelist)) # Set whitelist
            #regx = re.compile('|'.join(self._whitelist())) # Set whitelist
            for u in self._armadict.values():
                if regx.match(u.host) is None:                                        
                    Log.write('armageddon-kickban %s %s' % (u.nick, u.host))
                    self._bot.ban('*!*@' + u.host, False)
                    self._resetlist.append('*!*@' + u.host)
                    self._bot.kick(u.nick, 'ARMAGEDDON', False)    
                else:
                    Log.write('Saved %s %s' % (u.nick, u.host))
                        
            # Reset vars
            self._bot.deop(self._bot.channel, self._bot.nick)
            self._bot.flag('o', False)
            self.reset()
    
    def arma(self, usernames):
        '''
            @param usernames: The list of users to bring forth armageddon upon
            @summary: A toned down version of armageddon kickbanning only selected users 
        '''
        self.armageddon(0, usernames)
    
    def arma_recover(self, auto_op=True):
        '''
            @param auto_op: If set to true ensures that the bot is +o'd first
            @summary: Recovers from the armageddon by unbanning all the people previously banned
        '''
        if len(self._resetlist):
            if self._bot.has_flag('o'):
                self._recover = False
                for u in self._resetlist:
                    #Log.write('Unban %s' % u, 'D')
                    self._bot.unban(u, False)
                self._bot.deop(self._bot.channel, self._bot.nick)
                self._bot.flag('o', False)
            elif auto_op:
                self._recover = True
                self._bot.op(self._bot.channel, self._bot.nick)
            
    def output(self, nick, host, auth, powers, options):
        if options.whitelist is not None:            
            if options.whitelist:
                count = 0
                for hostmask in options.hostmasks:
                    if hostmask not in self._whitelist:
                        self._whitelist.append(hostmask)
                        count += 1
                self._bot.notice(nick, '%d hostmask(s) added' % count)
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
                self._bot.notice(nick, '%d hostmask(s) removed' % count)
                    
        elif options.list:
            self._bot.send_multiline(self._bot.notice, nick, 'Whitelisted hostnames are:\n' + '\n'.join([ '%2d) %s' % (i[0], i[1]) for i in zip(range(1,len(self._whitelist)+1), self._whitelist)]))
        else:
            if self._bot.has_status('arma'):
                if options.recover:
                    self.arma_recover()
                elif options.users:
                    self.arma(options.users)
                else:                    
                    self.armageddon(0)
                    self._bot.notice(nick, 'Commencing Armageddon!')
    
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
        Module for handling flag
    '''
    
    def build_meta(self, metadata):
        metadata.key = "flag"
        metadata.aliases = ["flag"]
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="flag", prefix_chars="+-", add_help=None, usage="flag [--help] +/-[hukbv]")
        parser.add_help_argument("--help", action="store_true", dest="help", default=False, help="Show this help")
        parser.add_flag("+h", "-h", dest="hear", help="Hear commands")
        parser.add_flag("+v", "-v", dest="voice", help="Voice results")        
        parser.add_flag("+k", "-k", dest="kick", help="Allow kicking")
        parser.add_flag("+b", "-b", dest="ban", help="Allow banning")        
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
                self._bot.notice(nick, 'Flags are: +' + ''.join(sorted(status)))
            else:                                  
                self._bot.notice(nick, 'No flag are set')
        else:
            self._bot.notice(nick, 'Flag(s) have been updated: ' + ''.join(sorted(status)))
        
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
        metadata.listeners = ["join", "nick"]
        
    def event(self, key, channel, user, args):
        if key == "join":
            if user.nick != self._bot.nick:
                self.enforce(user.nick, user.ident, user.host)
        elif key == "nick":
            if args != self._bot.nick:
                self.enforce(args, user.ident, user.host)
            
    def build_parser(self):
        parser = SimpleArgumentParser(prog="enforce")        
        parser.add_argument("-a", "--add", dest="add", choices=["kick", "ban", "arma"], help="Enforce a rule [Default: kick]", metavar="GROUP")
        parser.add_argument("-l", "--list", dest="list", action="store_true", help="List rules")
        parser.add_argument("-r", "--remove", dest="remove", choices=["kick", "ban", "arma"], help="Remove rule", metavar="GROUP")
        parser.add_argument("-x", "--regex", dest="regex", action="store_true", help="Rule is a regex")
        parser.add_argument("rule", nargs="*", help="Match rule (add), Group (list), Rule/Index (remove)", metavar="RULE|GROUP|INDEX")
        return parser
    
    def reload(self):
        reload(Enforce)
        
    def output(self, nick, host, auth, powers, options):
        if len(options.rule) == 0:
            if options.list:                
                if len(options.rule):
                    d = self._enforcer.rules(options.rule)
                    if d:
                        d = {options.rule: d}
                else:
                    d = self._enforcer.rules()
                    
                if d:
                    self._bot.send_multiline(self._bot.notice, nick, '\n'.join('Rules for "%s" are:\n%s' % (k, '\n'.join(['%s) %s %s' % (i[0], i[1][0], '[regex]' if i[1][1] else '') for i in zip(range(1, len(v)+1), v)])) for k, v in d.items()))
                else:
                    self._bot.notice(nick, 'No rules exist')
            else:
                self._bot.send_multiline(self._bot.notice, nick, self.help())
        else:
            options.rule = ' '.join(options.rule)
            if options.remove:               
                if options.rule[0] == '%':
                    try:
                        if self._enforcer.remove_at(options.remove, int(options.rule.lstrip('%')) - 1):
                            self._bot.notice(nick, 'Rule has been removed from group "%s"' % options.remove)
                    except ValueError:
                        if self._enforcer.remove(options.remove, options.rule):
                            self._bot.notice(nick, 'Rule has been removed from group "%s"' % options.remove)    
                else:
                    if self._enforcer.remove(options.remove, options.rule, options.regex):
                        self._bot.notice(nick, 'Rule has been removed from group "%s"' % options.remove)                                    
            else:                                                                    
                if self._enforcer.add(options.add, options.rule, options.regex):                                       
                    self._bot.notice(nick, 'Rule has been enforced to a new group "%s"' % options.add)
                else:  
                    self._bot.notice(nick, 'Rule has been enforced to group "%s"' % options.add)
            
    def enforce(self, nick, ident, host):        
        action = self._enforcer.enforce('%s!%s@%s' % (nick, ident, host))
        #m = self._regex_name.match(':'+user)
        if action == "kick":  
            self._bot.kick(nick, "The kinds of you aren't welcome here")
        elif action == "ban":
            self._bot.ban('*!*@'+host)
        elif action == "arma":
            self._bot.kickban(nick, '*!*@'+host, "The kinds of you aren't welcome here")#self._regex_name.search(':'+nick).group(1)])
            
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
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="users")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-a", "--add", dest="add", help="Add to this group", metavar="GROUP")        
        group.add_argument("-r", "--remove", dest="remove", help="Remove from this group", metavar="GROUP")        
        group.add_argument("-l", "--list", dest="list", action="store_true", help="List the users of a bot")        
        parser.add_argument("-t", "--auth", dest="auth", action="store_true", help="Authority level for group (0-255)")
        parser.add_argument("-p", "--power", dest="power", action="store_true", help="Specify the powers")
        parser.add_argument("hostmasks", nargs="*", help="User's hostmask or powers (-p) or auth (-t)", metavar="HOSTMASK|POWER|AUTH")
        return parser
    
    def output(self, nick, host, auth, powers, options):
        if options.add:
            if options.auth:                
                try:
                    a = int(options.hostmasks[0])
                    if a > self._bot.user_auth(user=host) and self._bot.role_add(options.add, a):                        
                        self._bot.notice(nick, 'The group "%s" has been added with authority level %d' % (options.add, a))
                    else:
                        self._bot.notice(nick, 'You can only add groups with lower auth than yours.')
                except ValueError:
                    self._bot.notice(nick, 'Invalid value for auth. Please use integers only.')
            elif self._bot.user_auth(role=options.add) > self._bot.user_auth(user=host):
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
                    self._bot.notice(nick, '%d hostmask(s) added as %s' % (count, options.add))
            else:                
                self._bot.notice(nick, 'You can only add users/powers to a lower group than yourself')
        elif options.list:
            if options.power:
                self._bot.send_multiline(self._bot.notice, nick, 'Powers are:\n' + '\n'.join(['[%s] : %s' % (k, ', '.join(['All'] if l is None else l)) for k, l in self._bot.power_list()]))            
            elif options.auth:
                self._bot.send_multiline(self._bot.notice, nick, 'Roles are:\n' + '\n'.join(['[%s] : %s' % (k, l) for k, l in self._bot.role_list()]))
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
                elif options.auth:
                    if self._bot.role_remove(options.remove):
                        self._bot.notice(nick, 'The group "%s" has been removed' % options.remove)
                else:
                    count = 0
                    for hostmask in options.hostmasks:
                        if self._bot.user_remove(options.remove, hostmask):
                            count += 1
                    self._bot.notice(nick, '%d hostmask(s) removed from %s' % (count, options.remove))
            else:
                self._bot.notice(nick, 'You can only remove users/powers of a lower group than yourself')
                

class ModManagerModule(BaseDynamicCommand):
    '''
        Handles the module management of the bot
    '''
    
    def build_meta(self, metadata):
        metadata.key = "module"
        metadata.aliases = ["module"]
        
    def build_parser(self):
        parser = SimpleArgumentParser(prog="module")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-e", "--enable", dest="enable", action="store_true", help="Enable the module")
        group.add_argument("-d", "--disable", dest="disable", action="store_true", help="Disable the module")
        group.add_argument("-r", "--reload", dest="reload", action="store_true", help="Reload the module [Default: All]")
        
        parser.add_argument("-l", "--list", dest="list", action="store_true", help="List the modules [Default: All]")
        
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-i", "--internal", dest="internal", action="store_true", help="Internal module")
        group.add_argument("-x", "--external", dest="external", action="store_true", help="External module")
        group.add_argument("-c", "--command", dest="command", action="store_true", help="Command module")
        
        parser.add_argument("keys", nargs="*", help="Module Key", metavar="KEY")
        return parser
    
    def output(self, nick, host, auth, powers, options):        
                
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
            self._bot.send_multiline(self._bot.notice, nick, s)       
        elif options.enable:
            for key in options.keys:
                if key != self.key:
                    if self._bot.module(key, mgr_type).enable():
                        self._bot.notice(nick, "The module '%s' has been enabled" % key)
                    else:
                        self._bot.notice(nick, "Module '%s' state unchanged" % key)
        elif options.disable:
            for key in options.keys:
                if key != self.key:            
                    self._bot.module(key, mgr_type).disable()
                    self._bot.notice(nick, "The module '%s' has been disabled" % key)        
        elif options.reload:
            if options.internal:
                if len(options.keys):
                    c = 0
                    for key in options.keys:                    
                        if self._bot.reload_extensions(key, 1):
                            c += 1
                    self._bot.notice(nick, '%d internal extension(s) have been reloaded' % c)
                else:
                    self._bot.reload_extensions(None, 1)
                    self._bot.notice(nick, 'All internal extensions have been reloaded')
            elif options.external:
                if len(options.keys):
                    c = 0
                    for key in options.keys:                    
                        if self._bot.reload_extensions(key, 2):
                            c += 1
                    self._bot.notice(nick, '%d external extension(s) have been reloaded' % c)
                else:
                    self._bot.reload_extensions(None, 2)
                    self._bot.notice(nick, 'All external extensions have been reloaded')
            elif options.command:
                if len(options.keys):
                    c = 0
                    for key in options.keys:                    
                        if self._bot.reload_commands(key):
                            c += 1
                    self._bot.notice(nick, '%d command(s) have been reloaded' % c)
                else:
                    self._bot.reload_commands()
                    self._bot.notice(nick, 'All commands have been reloaded')
            else:
                self._bot.reload_extensions(None, 0)
                self._bot.reload_commands()
                self._bot.notice(nick, 'All modules have been reloaded')
                
class SimpleLogModule(BaseDynamicCommand):
    '''
        Handles the logging task of the bot, logs are split on day
    '''
    def __init__(self, bot_state):
        super(SimpleLogModule, self).__init__(bot_state)
        self._format = 'QircLog[%Y.%m.%d]'              # Log format
        self._dir = 'logs-ignore/'                      # Log directory
        self._file = None
        self._buffer = ""
        self._date = datetime(1970, 1, 1)
        self._regex_name = re.compile(r'^:?([^!]+)!([^@]+)@(.*)$')
        if not os.path.exists(self._dir):
            os.makedirs(self._dir)        
            
    def build_meta(self, metadata):
        metadata.key = "log"
        metadata.aliases = ["log"]
        metadata.listeners = ["join", "nick", "mode", "msg", "privmsg", "notice", "broadcast", "kick", "part", "quit", "botquit", "exit"]#, "ping", "pong", "motd_end"]
        
    def event(self, key, channel, user, args):
        if key == "join":
            self.joined(user, channel)
        elif key == "nick":
            self.nick(user, args)
        elif key == "mode":
            self.mode(user, channel, '%s%s' % (args[0], args[1]), args[2])
        elif key == "msg":
            self.msg(user, channel, args)
        elif key == "privmsg":
            self.msg(user, channel, args)
        elif key == "notice":
            self.msg(user, channel, args, notice=True)
        elif key == "broadcast":
            self.msg(user, channel, args, broadcast=True)
        elif key == "kick":
            self.kicked(channel, user, args[0], args[1])
        elif key == "part":
            self.parted(user, channel, args)
        elif key == "quit":
            self.quit(user, args)
        elif key == "botquit":
            self.quit(user, args)
        elif key == "exit" or key == "reload":
            self.close()
        elif key == "motd_end":
            self.log("END MOTD")
        elif key == "ping":
            self.log("PING: %s" % args)
        elif key == "pong":
            self.log("PONG: %s [%s]" % (args[0], args[1]))
            
    #def get_user(self, nick, ident, host):
    #    return '%s!%s@%s' % (nick, ident, host)
    
    def enabled(self, value=None):
        if value is None:
            return self._logging
        else:
            self._logging = value
            
    
    #def parse_name(self, user):
    #    return self._regex_name.match(user).groups()
    
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
        if self.is_enabled():
            now = datetime.utcnow()            
            #d = now - self._date
            if self._date.date() != now.date():
                self._date = now
                self.close()
                Log.write('Opening Log: ' + os.path.join(self._dir, datetime.strftime(self._date, self._format)))
                self._file = open(os.path.join(self._dir, datetime.strftime(self._date, self._format)), "a")
                        
            self._buffer += datetime.strftime(now, "[%H:%M:%S] ") + msg + '\n'
            if len(self._buffer) > 256:
                self._file.write(self._buffer)
                self._file.flush()
                self._buffer = ""             
    
    def joined(self, user, channel):
        self.log("JOIN: %s joined %s" % (user, channel))
    
    def kicked(self, channel, user, source, reason):        
        self.log("KICK: %s was kicked by %s from %s. Reason: %s" % (user, source, channel, reason))
    
    def banned(self, user, channel):
        self.log("BAN: %s banned from %s" % (user, channel))
    
    def parted(self, user, channel, reason):
        self.log("PART: %s parted from %s. Reason: %s" % (user, channel, reason))
    
    def quit(self, user, reason):
        self.log("QUIT: %s quit. Reason: %s" % (user, reason))
    
    def mode(self, source, channel, flags, users):
        if users:
            self.log("MODE: %s set mode %s for %s on %s" % (source, flags, ', '.join(users), channel))
        else:
            self.log("MODE: %s set mode %s on %s" % (source, flags, channel))
        
    def nick(self, user, new_nick):
        self.log("NICK: %s is now known as %s" % (user, new_nick))
    
    def msg(self, user, channel, msg, notice=False, broadcast=False):        
        if msg.startswith('\x01ACTION '):
            self.log("ACTION: %s %s" % (user.nick, ''.join(msg[len('\x01ACTION '):-1])))
        else:
            if notice:                
                self.log("<%s whispers> %s" % (user.nick, msg))
            elif broadcast:
                self.log("%s : %s" % (user.nick, msg))
            elif channel:
                self.log("<%s : %s> %s" % (user.nick, channel, msg))
            else:
                self.log("<%s> %s" % (user.nick, msg))    