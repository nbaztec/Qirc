'''
Created on Jun 8, 2012
@author: Nisheeth
'''

from collections import OrderedDict
import re
class redict(object):
    '''
        @summary: Class to store regexes as dictionary keys
    '''
    def __init__(self):
        self._dict = OrderedDict()
    
    def __setitem__(self, key, value):        
        self._dict[key] = [re.compile(key[0], key[1]), value]        
        
    def __getitem__(self, key):
        return self._dict[key]
    
    def __delitem__(self, key):
        self._dict.pop(key)
    
    def __contains__(self, k):
        return k in self._dict.__contains__(k)
    
    has_key = __contains__
    
    def __iter__(self):
        for k in self._dict.iterkeys():
            yield k
    
    iterkeys = __iter__
    
    def iteritems(self):       
        for (k,v) in self._dict.iteritems():
            yield (k, v) 
    
    def itervalues(self):       
        for v in self._dict.itervalues():
            yield v            
        
    # Extended functions    
    def iter_regex(self): 
        for (v1,v2) in self._dict.itervalues():
            yield (v1, v2)        