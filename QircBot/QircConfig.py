'''
Created on Dec 27, 2012

@author: Nisheeth
'''
from Util.Config import ConfigManager
import os
from collections import OrderedDict

class Object(object):
    def __str__(self):                    
        return '{%s}' % ', '.join(["'%s': %s" % (k,v) for k,v in self.__dict__.items()])

class QircConfig(object):
    '''
    Handles configuration from QircBot
    '''

    _file = 'qirc.conf'

    def __new__(cls, section=None, force=False):
        '''
        Constructor
        '''        
        if not os.path.exists(cls._file) or force:
            cls.create()
        return cls.read(section)    
                
    @classmethod
    def read(cls, section=None):        
        if os.path.exists(cls._file):
            d = ConfigManager.read_config(cls._file)
            if d:
                config = d
                config['server']['port'] = int(config['server']['port'])
                config['bot']['attempt-nick'] = config['bot']['nick']
                config['bot']['owner'] = config['bot']['owner'].split(' ')
                
                config['startup']['channels'] = config['startup']['channels'].split(' ')
                config['startup']['notice-to'] = config['startup']['notice-to'].split(' ')
                                
                if len(config['bot']['password']) == 0:
                    config['bot']['password'] = None
                    
                if section:
                    if config.has_key(section):
                        return config[section]
                else:
                    return config
        return None
           
    @classmethod 
    def create(cls):
        d = OrderedDict()
        d['server'] = OrderedDict()
        d['server']['url'] = 'irc.freenode.net'
        d['server']['port'] = '6667'
                    
        d['bot'] = OrderedDict()
        d['bot']['nick'] = 'QircBug'
        d['bot']['ident'] = 'QircBug'
        d['bot']['realname'] = 'QirckyBotBug'
        d['bot']['password'] = ''
        d['bot']['owner'] = 'unaffiliated/nbaztec'
        
        d['startup'] = OrderedDict()
        d['startup']['channels'] = '#nbaztec'
        d['startup']['notice-to'] = 'nbaztec'
        d['startup']['notice-msg'] = 'Qirc is now online.'
        
        #d['global'] = OrderedDict()
        #d['global']['flags'] = 'ubhkv'
        #d['global']['logging'] = 'true'
        
        d['logs'] = OrderedDict()
        d['logs']['dir'] = 'logs-ignore/'
        d['logs']['file-format'] = '{timestamp:[%Y-%m-%d]}{channel}.log'
        d['logs']['buffer-len'] = '256'
        
        ConfigManager.write_config(cls._file, d)

        