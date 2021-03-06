'''
Created on Jun 8, 2012
@author: Nisheeth
@summary: Provides calculation provisions using various sites
'''

import re
import urllib
import urllib2
from Util.BeautifulSoup import BeautifulSoup
from Util.Config import ConfigManager
from Util import htmlx
from Util.Log import Log
import json

config = ConfigManager.read_config('extensions.conf', 'wolfram')

#config = {
#            'wolf'      : 'RU4KX6-XJY2PPE93Y',
#        }


def wolfram(query):
    '''
        @param query: Query for calculation
        @summary: Performs calculation on Wolfram Alpha and returns the results
    '''    
    try:        
        response = urllib2.urlopen('http://api.wolframalpha.com/v2/query?appid=%s&input=%s&format=plaintext' % (config['app-id'], urllib.quote(query)))        
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)            
        out = []
        primary_items = soup.findAll('pod', attrs={'primary': 'true'})        
        for primary in primary_items:
            out.append(htmlx.unescape(''.join(primary.find('plaintext').findAll(text=True))))
        if len(out):
            return re.sub(r'^rupee\s*', 'Rs. ', (', '.join(out))).encode('utf-8')
        else:
            return None
    except Exception:
        Log.error()
        return None        
    
def googlecalc(query):
    '''
        @param query: Query for calculation
        @summary: Performs calculation on Google Calc and returns the results
    '''    
    try:        
        response = urllib2.urlopen('http://www.google.com/ig/calculator?hl=en&q=%s' % urllib.quote(query))
        page = response.read().replace('\xa0', ' ')                 # Convert &nbsp; to actual space
        page = re.sub(r'(\d+)(\s|\xa0)(\d+)', r'\1,\3', page)       # Replace spaces between numbers by comma
        response.close()        
        result = json.loads(htmlx.fixjson(page))    
        if result['error'] == '':
            return ('%s = %s' % (htmlx.unescape(result['lhs']), htmlx.unescape(result['rhs']))).encode('utf-8')
        else:
            return None
    except Exception:
        Log.error()
        return None        