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

def to_celcius(f):
    return (float(f)-32)*5/9

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
        response = urllib2.urlopen('http://api.wolframalpha.com/v2/query?appid=XXXX&input=%s&format=plaintext' % urllib.quote(query))        
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)            
        primary_item = soup.find('pod', attrs={'primary': 'true'})
        #wolf_output = []
        #for item in items:
        #    try:
        #        wolf_output.append(item.find(text=True).replace('\n', ' '))
        #    except:
        #        pass     
        #if len(wolf_output):               
        #    return ', '.join(wolf_output)
        if primary_item:
            return ''.join(primary_item.findAll(text=True))
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
        response = urllib2.urlopen('https://www.googleapis.com/customsearch/v1?key=XXXX&cx=013036536707430787589:_pqjad5hr1a&q=%s&alt=atom&num=1' % urllib.quote(query))        
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
        response = urllib2.urlopen('https://www.googleapis.com/customsearch/v1?key=XXXX&cx=013036536707430787589:_pqjad5hr1a&q=%s&alt=atom&num=1&siteSearch=thinkdigit.com/forum/' % urllib.quote(query))        
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
    
def urbandefine(term):    
    '''
        @var term: Term for searching
        @summary: Performs a urban dictionary search and returns the first result
    '''  
    try:       
        response = urllib2.urlopen('http://www.urbandictionary.com/define.php?term=%s' % urllib.quote(term))        
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)            
        item_1 = soup.find('table', attrs={'id': 'entries'}).find('td', attrs={'class': 'text'})
        define = htmlx.unescape(''.join(item_1.find('div', attrs={'class': 'definition'}).findAll(text=True)))
        example = htmlx.unescape(''.join(item_1.find('div', attrs={'class': 'example'}).findAll(text=True)))            
        return "%s: %s, Eg: %s" % (term, define, example)
    except Exception, e:
        print 'Error', e
        return None

def weather(place): 
    '''
        @var term: Term for searching
        @summary: Performs a urban dictionary search and returns the first result
    '''     
    try:
        response = urllib2.urlopen('http://www.google.com/ig/api?weather=%s' % urllib.quote(place))        
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)
        current = soup.find('current_conditions')
        return '%s: %s at %sC, %s, %s' % (soup.find('forecast_information').find('city')['data'], current.find('condition')['data'], current.find('temp_c')['data'], current.find('humidity')['data'], current.find('wind_condition')['data'])          
    except Exception, e:
        print 'Error', e
        return None
    
def forecast(place): 
    '''
        @var term: Term for searching
        @summary: Performs a urban dictionary search and returns the first result
    '''     
    try:
        response = urllib2.urlopen('http://www.google.com/ig/api?weather=%s' % urllib.quote(place))        
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)
        forecasts = soup.findAll('forecast_conditions')
        r = []
        for f in forecasts:
            r.append('%s on %s %dC-%dC' % (f.find('condition')['data'], f.find('day_of_week')['data'], to_celcius(f.find('low')['data']), to_celcius(f.find('high')['data'])))
        return '%s: %s' % (soup.find('forecast_information').find('city')['data'], ' | '.join(r))          
    except Exception, e:
        print 'Error', e
        return None
        
def translate(msg):    
    '''
        @var msg: Message to translate
        @summary: Translates a query into destination language using Microsoft Translate
        @attention: TODO
    '''  
    try:        
        req = urllib2.Request('http://translate.google.com/#auto|en|%s.' % urllib.quote(msg))
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.52 Safari/536.5')
        response = urllib2.urlopen(req)        
        page = response.read()        
        print page                    
        response.close()
        soup = BeautifulSoup(page)            
        trans = ''.join(soup.find('span', attrs={'id': 'result'}).findAll(text=True))            
        return "%s -> %s" % (msg, trans)
    except Exception, e:
        print 'Error', e
        return None        
