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
from Util.Log import Log

appid = {
            'google'    : '',
            'wolf'      : '',
            'ipinfo'    : ''
        }

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
        return ("%s [%s]" % (htmlx.unescape(desc.replace('\n', ' ')), url)).encode('utf-8')
    except Exception, e:
        Log.write(e, 'E')
        return None            

def wolfram(query):
    '''
        @var query: Query for calculation
        @summary: Performs calculation on Wolfram Alpha and returns the results
    '''    
    try:        
        response = urllib2.urlopen('http://api.wolframalpha.com/v2/query?appid=%s&input=%s&format=plaintext' % (appid['wolf'], urllib.quote(query)))        
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)            
        out = []
        primary_items = soup.findAll('pod', attrs={'primary': 'true'})        
        for primary in primary_items:
            out.append(htmlx.unescape(''.join(primary.find('plaintext').findAll(text=True))))
        if len(out):
            return (', '.join(out)).encode('utf-8')
        else:
            return None
    except Exception, e:
        Log.write(e, 'E')
        return None
        
def google(query, num=1):    
    '''
        @var query: Query for searching
        @var num: Return the (n)th result
        @summary: Performs a Google search and returns the first result
        @attention: Google's description requires unescaping twice
    '''  
    try:        
        response = urllib2.urlopen('https://www.googleapis.com/customsearch/v1?key=%s&cx=013036536707430787589:_pqjad5hr1a&q=%s&alt=atom&num=%d' % (appid['google'], urllib.quote(query), num))
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)            
        item_1 = soup.findAll('entry')[num-1]
        url =  ''.join(item_1.find('id').find(text=True))
        desc = htmlx.unescape(htmlx.unescape(re.sub(r'&lt;[^&]+&gt;','',item_1.find('summary').find(text=True)))) 
        return ("[%s], %s" % (url, desc)).encode('utf-8')
    except Exception, e:
        Log.write(e, 'E')
        return None
    
def tdf(query):    
    '''
        @var query: Query for searching
        @summary: Performs a Google search on thinkdigit forum and returns the first result
    '''  
    try:        
        response = urllib2.urlopen('https://www.googleapis.com/customsearch/v1?key=%s&cx=013036536707430787589:_pqjad5hr1a&q=%s&alt=atom&num=1&siteSearch=thinkdigit.com/forum/' % (appid['google'], urllib.quote(query)))        
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)            
        item_1 = soup.findAll('entry')[0]
        url =  ''.join(item_1.find('id').find(text=True))            
        desc = htmlx.unescape(re.sub(r'&lt;[^&]+&gt;','',item_1.find('summary').find(text=True)))     
        return ("[%s], %s" % (url, desc)).encode('utf-8')
    except Exception, e:
        Log.write(e, 'E')
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
    except Exception, e:
        Log.write(e, 'E')
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
        return ('%s: %s at %sC, %s, %s' % (soup.find('forecast_information').find('city')['data'], current.find('condition')['data'], current.find('temp_c')['data'], current.find('humidity')['data'], current.find('wind_condition')['data'])).encode('utf-8')          
    except Exception, e:
        Log.write(e, 'E')
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
        return ('%s: %s' % (soup.find('forecast_information').find('city')['data'], ' | '.join(r))).encode('utf-8')          
    except Exception, e:
        Log.write(e, 'E')
        return None
    
def iplocate(ip): 
    '''
        @var ip: The IP address
        @summary: Performs a IP lookup and obtains the location of the user
    '''     
    try:
        response = urllib2.urlopen('http://api.ipinfodb.com/v3/ip-city/?key=%s&format=xml&ip=%s' % (appid['ipinfo'], urllib.quote(ip)))        
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)
        reply = soup.find('response')
        if reply.find('statuscode').find(text=True) == "OK":            
            r_lat = str((reply.find('latitude').find(text=True)))
            r_long = str(reply.find('longitude').find(text=True))
            return '%s belongs to %s' % (ip, geo(r_lat, r_long))
        else:
            return None
    except Exception, e:
        Log.write(e, 'E')
        return None
        
def geo(latitude, longitude): 
    '''
        @var latitude: The latitude of location
        @var longitude: The longitude of location
        @summary: Performs a reverse geo lookup on Google Maps API
    '''     
    try:
        response = urllib2.urlopen('http://maps.googleapis.com/maps/api/geocode/xml?latlng=%s,%s&sensor=false' % (latitude, longitude))        
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)
        address = str(soup.find('result').find('formatted_address').find(text=True))        
        return '[%s, %s] : %s' % (latitude, longitude, address)        
    except Exception, e:
        Log.write(e, 'E')
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
        Log.write(page)                    
        response.close()
        soup = BeautifulSoup(page)            
        trans = ''.join(soup.find('span', attrs={'id': 'result'}).findAll(text=True))            
        return ("%s -> %s" % (msg, trans)).encode('utf-8')
    except Exception, e:
        Log.write(e, 'E')
        return None        