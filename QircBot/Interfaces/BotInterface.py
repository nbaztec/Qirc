'''
Created on Jul 30, 2012

@author: Nisheeth
'''

class BaseInterface(object):
    '''
        Base Class
    '''
    def __init__(self, bot):
        '''
            @param say: An output function to print the regular messages
            @param notice: An output function to print the whisper messages
            @param action: An output function to print the self actions
        '''
        self.params = bot.params
        self.userlist = bot.current_userlist
        self.request_names = bot.request_userlist
    
    @property
    def nick(self):
        return self.params['nick']
    
    @property
    def channel(self):
        if len(self.params['chan']):
            return self.params['chan'][0]
        else:
            return ''
        
    @property
    def names(self):        
        return self.userlist()

class VerbalInterface(BaseInterface):
    '''
        Presents a verbal-only interface of bot
    '''
    def __init__(self, bot):
        '''
            @param bot: An instance of QircBot
        '''
        BaseInterface.__init__(self, bot)
        self.say = bot.say
        self.msg = bot.msg
        self.notice = bot.notice
        self.action = bot.action
        self.send_multiline = bot.send_multiline        
        self.has_status = bot.get_status
        self.has_flag = bot.get_flag
        self.db = bot.get_sqlite_db()
    
    @property
    def sqlite_db(self):
        return self.db
   
class AuthorityInterface(BaseInterface):
    '''
        Presents a authority-only interface of bot
    '''    
    def __init__(self, bot):
        '''
            @param bot: An instance of QircBot
        '''
        self.kick = bot.kick
        self.ban = bot.ban
        self.unban = bot.unban
        self.kickban = self.arma = bot.kickban
        self.status = bot.set_status
        self.flag = bot.set_flags
        
class EnforcerInterface(VerbalInterface, AuthorityInterface):
    '''
        Presents a authority-only interface of bot
    ''' 
    def __init__(self, bot):
        '''
            @param bot: An instance of QircBot
        '''
        VerbalInterface.__init__(self, bot)
        AuthorityInterface.__init__(self, bot)
        self.op = bot.op
        self.deop = bot.deop
        
class PrivilegedInterface(EnforcerInterface):
    '''
        Presents a authority-only interface of bot
    ''' 
    def __init__(self, bot):
        '''
            @param bot: An instance of QircBot
        '''
        EnforcerInterface.__init__(self, bot) 
        self.join = bot.join
        self.part = bot.part
        self.disconnect = bot.disconnect
        self.change_nick = bot.nick
        self.ghost = bot.ghost
        self.identify = bot.identify
        self.role_power = bot.role_power
        self.power_list = bot.power_list
        self.role_list = bot.role_list
        self.role_add = bot.role_add
        self.role_remove = bot.role_remove
        self.user_add = bot.user_add
        self.user_remove = bot.user_remove
        self.user_auth = bot.user_auth
        self.user_list = bot.user_list        
        self.module = bot.get_module
        self.modules = bot.get_modules
        self.module_keys = bot.get_module_keys
        self.add_retry_channel = bot.add_retry_channel
        self.remove_retry_channel = bot.remove_retry_channel
        self.retry_channels = bot.retry_channels 
        self.reload_extensions = bot.reload_extensions        
        self.reload_commands = bot.reload_commands
        self.save_state = bot.save_state
        
class CompleteInterface(PrivilegedInterface):
    '''
        Presents a complete interface of bot
    ''' 
    def __init__(self, bot):
        '''
            @param bot: An instance of QircBot
        '''
        PrivilegedInterface.__init__(self, bot)   
        self.close = bot.close
        self.send = bot.send