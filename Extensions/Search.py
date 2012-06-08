'''
Created on Jun 8, 2012
@author: Nisheeth
@summary: Provides searches for various sites
'''

import urllib
import urllib2
import re
from Util.BeautifulSoup import BeautifulSoup
from Util import htmlx

def wiki(word):
    '''
        @var word: Word to search for
        @summary: Searches for a word on Wikipedia and returns an abstract
    '''
    try:        
        response = urllib2.urlopen('http://en.wikipedia.org/w/api.php?action=opensearch&search=%s&format=xml' % urllib.quote(word))        
        page = response.read()                        
        response.close()
        soup = BeautifulSoup(page)            
        item_1 = soup.find('item')
        desc = ''.join(item_1.find('description').find(text=True))
        url = ''.join(item_1.find('url').find(text=True))
        return "%s [%s]" % (desc.replace('\n', ' '), url)
    except Exception, e:
        print e
        return None            

def wolfram(query):
    '''
        @var query: Query for calculation
        @summary: Performs calculation on Wolfram Alpha and returns the results
    '''    
    try:        
        response = urllib2.urlopen('http://api.wolframalpha.com/v2/query?appid=RU4KX6-XJY2PPE93Y&input=%s&format=plaintext' % urllib.quote(query))        
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)            
        items = soup.findAll('plaintext')
        wolf_output = []
        for item in items:
            try:
                wolf_output.append(item.find(text=True).replace('\n', ' '))
            except:
                pass     
        if len(wolf_output):               
            return ', '.join(wolf_output)
        else:
            return None
    except Exception, e:
        print 'Error', e
        return None
        
def google(query):    
    '''
        @var query: Query for searching
        @summary: Performs a Google search and returns the first result
    '''  
    try:        
        response = urllib2.urlopen('https://www.googleapis.com/customsearch/v1?key=AIzaSyAMajmwMaD4uPv1EuXn_WzC-9T61GZW5gw&cx=013036536707430787589:_pqjad5hr1a&q=%s&alt=atom&num=1' % urllib.quote(query))        
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)            
        item_1 = soup.findAll('entry')[0]
        url =  ''.join(item_1.find('id').find(text=True))            
        desc = htmlx.unescape(re.sub(r'&lt;[^&]+&gt;','',item_1.find('summary').find(text=True))) 
        return "[%s], %s" % (url, desc)
    except Exception, e:
        print 'Error', e
        return None
    
def tdf(query):    
    '''
        @var query: Query for searching
        @summary: Performs a Google search on thinkdigit forum and returns the first result
    '''  
    try:        
        response = urllib2.urlopen('https://www.googleapis.com/customsearch/v1?key=AIzaSyAMajmwMaD4uPv1EuXn_WzC-9T61GZW5gw&cx=013036536707430787589:_pqjad5hr1a&q=%s&alt=atom&num=1&siteSearch=thinkdigit.com/forum/' % urllib.quote(query))        
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)            
        item_1 = soup.findAll('entry')[0]
        url =  ''.join(item_1.find('id').find(text=True))            
        desc = htmlx.unescape(re.sub(r'&lt;[^&]+&gt;','',item_1.find('summary').find(text=True)))     
        return "[%s], %s" % (url, desc)
    except Exception, e:
        print 'Error', e
        return None
        