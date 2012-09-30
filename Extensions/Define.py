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
            'google'    : 'XXXX',
            'stands4'   : {'userid': 'XXXX', 'token': 'XXXX'}
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
    
def dictionary(term, num=1):
    '''
        @var term: Term for searching
        @var num: Return the (n)th result
        @summary: Performs a abbreviations.com dictionary search and returns the first result
    '''  
    try:              
        response = urllib2.urlopen('http://www.stands4.com/services/v2/defs.php?uid=%s&tokenid=%s&word=%s' % (appid['stands4']['userid'], appid['stands4']['token'], urllib.quote(term)))        
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)            
        items = soup.findAll('result')
        item = items[num-1]
        term = htmlx.unescape(''.join(item.find('term').findAll(text=True)))
        part = htmlx.unescape(''.join(item.find('partofspeech').findAll(text=True)))
        definition = htmlx.unescape(''.join(item.find('definition').findAll(text=True)))
        example = htmlx.unescape(''.join(item.find('example').findAll(text=True)))
        return ('%s (%s), %s. Eg: %s' % (term, part, definition, example)).encode('utf-8')        
    except Exception:
        Log.error()
        return None 

def synonyms(term, num=1):
    '''
        @var term: Term for searching
        @var num: Return the (n)th result
        @summary: Performs a abbreviations.com synonym search and returns the results
    '''  
    try:              
        response = urllib2.urlopen('http://www.stands4.com/services/v2/syno.php?uid=%s&tokenid=%s&word=%s' % (appid['stands4']['userid'], appid['stands4']['token'], urllib.quote(term)))        
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)            
        items = soup.findAll('result')
        item = items[num-1]        
        part = htmlx.unescape(''.join(item.find('partofspeech').findAll(text=True)))        
        syno = htmlx.unescape(''.join(item.find('synonyms').findAll(text=True)))
        return ('(%s) %s' % (part, syno)).encode('utf-8')        
    except Exception:
        Log.error()
        return None 

#def antonym(term, num=1):
#    '''
#        @var term: Term for searching
#        @var num: Return the (n)th result
#        @summary: Performs a abbreviations.com dictionary search and returns the first result
#    '''  
#    pass

def quote(term, search=False, author=False, num=1):
    '''
        @var term: Term for searching
        @var num: Return the (n)th result
        @summary: Returns a quote from abbreviations.com
    '''      
    try:
        
        if search:
            srch = "SEARCH"
        elif author:
            srch = "AUTHOR"
        else:
            srch = "RANDOM"                
        response = urllib2.urlopen('http://www.stands4.com/services/v2/quotes.php?uid=%s&tokenid=%s&searchtype=%s&query=%s' % (appid['stands4']['userid'], appid['stands4']['token'], srch, urllib.quote(term)))        
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)            
        items = soup.findAll('result')
        item = items[num-1]
        quote = htmlx.unescape(''.join(item.find('quote').findAll(text=True))).strip('"')
        author = htmlx.unescape(''.join(item.find('author').findAll(text=True)))        
        return ('"%s" -%s' % (quote, author)).encode('utf-8')        
    except Exception:
        Log.error()
        return None        