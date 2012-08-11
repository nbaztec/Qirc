'''
Created on Jul 17, 2012

@author: Nisheeth
'''
import re

class Enforcer(object):
    '''
    Calls a function depending upon the matched string
    '''

    def __init__(self):
        self._rules = {}
        self.set = self.add        
        pass
    
    def add(self, rule, action, tag):
        self._rules[rule] = (action, tag)
        
    def remove(self, rule):
        try:
            self._rules.pop(rule)
            return True
        except KeyError:
            return False
        
    def remove_at(self, index):
        try:
            i = 0
            for k in self._rules.keys():
                if i == index:
                    self._rules.pop(k)
                    return True
                    break
                else:
                    i += 1
        except:
            pass
        return False
        
    def get_rules(self):
        return self._rules.keys()
    
    def get_items(self):
        return self._rules.items()
    
    def enforce(self, string):
        for k,v in self._rules.items():
            if re.match(k, string):
                v[0](string)