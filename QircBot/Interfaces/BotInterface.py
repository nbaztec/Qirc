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
            @var say: An output function to print the regular messages
            @var notice: An output function to print the whisper messages
            @var action: An output function to print the self actions
        '''
        self.params = bot.params
        pass
    
    @property
    def botnick(self):
        return self.params['nick']
    
    @property
    def channel(self):
        return self.params['chan']    

class VerbalInterface(BaseInterface):
    '''
        Presents a verbal-only interface of bot
    '''
    def __init__(self, bot):
        '''
            @var bot: An instance of QircBot
        '''
        BaseInterface.__init__(self, bot)
        self.say = bot.say
        self.msg = bot.msg
        self.notice = bot.notice
        self.action = bot.action
        self.send_multiline = bot.send_multiline        
        self.has_status = bot.get_status_flag
                    
class AuthorityInterface(BaseInterface):
    '''
        Presents a authority-only interface of bot
    '''    
    def __init__(self, bot):
        '''
            @var bot: An instance of QircBot
        '''
        self.kick = bot.kick
        self.ban = bot.ban
        self.unban = bot.unban
        self.kickban = self.arma = bot.arma
        self.arma_recover = bot.arma_recover
        self.status = bot.status_flag  
        
class EnforcerInterface(VerbalInterface, AuthorityInterface):
    '''
        Presents a authority-only interface of bot
    ''' 
    def __init__(self, bot):
        '''
            @var bot: An instance of QircBot
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
            @var bot: An instance of QircBot
        '''
        EnforcerInterface.__init__(self, bot) 
        self.armageddon = bot.armageddon
        self.join = bot.join
        self.disconnect = bot.disconnect
        self.nick = bot.nick
        self.ghost = bot.ghost
        self.identify = bot.identify
        self.role_power = bot.role_power
        self.power_list = bot.power_list
        self.user_add = bot.user_add
        self.user_remove = bot.user_remove
        self.user_auth = bot.user_auth
        self.user_list = bot.user_list        
        self.module = bot.get_module
        self.logger = bot._logger
        
class CompleteInterface(PrivilegedInterface):
    '''
        Presents a complete interface of bot
    ''' 
    def __init__(self, bot):
        '''
            @var bot: An instance of QircBot
        '''
        PrivilegedInterface.__init__(self, bot)   
        self.close = bot.close
        self.send = bot.send