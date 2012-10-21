'''
Created on Jul 17, 2012

@author: Nisheeth
'''
import re
import fnmatch

class Enforcer(object):
    '''
    Calls a function depending upon the matched string
    '''

    def __init__(self):
        self._rules = { }
                        #'arma': [],
                        #'ban' : [],
                        #'kickban': []
                        #}
        
        self.set = self.add
        #self._regex_matcher = re.compile(r'(?<!\\)((?:\\\\)*)([*?])')
    
    #def make_regex(self, simple_rule):        
    #    return self._regex_matcher.sub('\1.\2', simple_rule)
    
    def add(self, action, rule, is_regex=False):
        '''
            @return: True if new group was created, False otherwise
        '''
        if self._rules.has_key(action):
            self._rules[action].append((rule, is_regex))
            return False
        else:
            self._rules[action] = [(rule, is_regex)]
            return True
        
    def remove(self, action, rule, is_regex):
        try:            
            self._rules[action].remove((rule, is_regex))
            if len(self._rules[action]) == 0:
                self._rules.pop(action)
            return True
        except KeyError:
            return False
        except ValueError:
            return False
        
    def remove_at(self, action, index):        
        try:
            self._rules[action].pop(index)
            if len(self._rules[action]) == 0:
                self._rules.pop(action)
            return True
        except KeyError:
            return False
        except ValueError:
            return False

    def rules(self, action=None):
        if action:
            return self._rules[action] if self._rules.has_key(action) else None;
        else:
            return self._rules;
    
    def enforce(self, string):
        for k, v in self._rules.items():
            for r, x in v:
                if x:
                    if re.match(r, string):
                        return k
                else:
                    if fnmatch.fnmatch(string, r):
                        return k
        return None