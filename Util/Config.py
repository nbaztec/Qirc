'''
Created on Jan 1, 2013

@author: Nisheeth
'''
from ConfigParser import RawConfigParser
import codecs
import os

class ConfigManager(object):
    '''
    classdocs
    '''

    @classmethod
    def read_config(cls, filename, section=None):
        if os.path.exists(filename):
            parser = RawConfigParser()
            with codecs.open(filename, 'r', encoding='utf-8') as f:
                parser.readfp(f)
                                 
            d = {}
            for s in parser.sections():                
                d[s] = {}
                for t in parser.items(s):
                    d[s][t[0]] = t[1]
            if section:
                return d[section]
            else:
                return d
        
    @classmethod
    def write_config(cls, filename, config):
        with codecs.open(filename, 'w', encoding='utf-8') as f:
            parser = RawConfigParser()
            for sec, cfg in config.items():
                parser.add_section(sec)
                for k, v in cfg.items():
                    parser.set(sec, k, v)
            parser.write(f)
        