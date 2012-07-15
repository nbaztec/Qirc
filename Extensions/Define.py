'''
Created on Jun 8, 2012
@author: Nisheeth
@summary: Provides searches for word definitions
'''

import urllib
import urllib2
import re
from Util.BeautifulSoup import BeautifulSoup
from Util import htmlx
from Util.Log import Log

appid = {
            'google'    : 'AIzaSyAMajmwMaD4uPv1EuXn_WzC-9T61GZW5gw',
        }

def googledefine(query, num=1):    
    '''
        @var query: Query for searching
        @var num: Return the (n)th result
        @summary: Performs a Google search and returns the first result
        @attention: Google's description requires unescaping twice
    '''  
    try:        
        response = urllib2.urlopen('https://www.googleapis.com/customsearch/v1?key=%s&cx=013036536707430787589:_pqjad5hr1a&q=define+%s&alt=atom&num=%d' % (appid['google'], urllib.quote(query), num))
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)            
        item_1 = soup.findAll('entry')[num-1]
        url =  ''.join(item_1.find('id').find(text=True))
        desc = htmlx.unescape(htmlx.unescape(re.sub(r'&lt;[^&]+&gt;','',item_1.find('summary').find(text=True)))) 
        return ("%s, %s" % (url, desc)).encode('utf-8')
    except Exception:
        Log.error()
        return None    

def urbandefine(term, num=1):    
    '''
        @var term: Term for searching
        @var num: Return the (n)th result
        @summary: Performs a urban dictionary search and returns the first result
    '''  
    try:       
        response = urllib2.urlopen('http://www.urbandictionary.com/define.php?term=%s' % urllib.quote(term))        
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)            
        items = soup.find('table', attrs={'id': 'entries'}).findAll('td', attrs={'class': 'text', 'id': re.compile('entry_\d+')})
        item = items[num-1]
        define = htmlx.unescape(''.join(item.find('div', attrs={'class': 'definition'}).findAll(text=True)))
        example = htmlx.unescape(''.join(item.find('div', attrs={'class': 'example'}).findAll(text=True)))
        if len(example):            
            example = ", Eg: " + example
        return ("%s: %s%s" % (term, define, example)).encode('utf-8')        
    except Exception:
        Log.error()
        return None