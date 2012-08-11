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
            'google'    : 'AIzaSyAMajmwMaD4uPv1EuXn_WzC-9T61GZW5gw',
        }


def wiki(word, num=1, single=False):
    '''
        @var word: Word to search for
        @var num: Get the nth result
        @var single: Get only the title        
        @summary: Searches for a word on Wikipedia and returns an abstract
    '''
    try:        
        response = urllib2.urlopen('http://en.wikipedia.org/w/api.php?action=opensearch&search=%s&format=xml' % urllib.quote(word))        
        page = response.read()                        
        response.close()
        soup = BeautifulSoup(page)            
        item_1 = soup.findAll('item')[num-1]
        if single:
            desc = ''.join(item_1.find('text').find(text=True))
        else:
            desc = ''.join(item_1.find('description').find(text=True))
        url = ''.join(item_1.find('url').find(text=True))        
        return ("%s, %s" % (url, htmlx.unescape(desc.replace('\n', ' ')))).encode('utf-8')
    except Exception:
        Log.error()
        return None            
        
def google(query, num=1, single=False):    
    '''
        @var query: Query for searching
        @var num: Get the nth result
        @var single: Get only the title
        @summary: Performs a Google search and returns the first result
        @attention: Google's description requires unescaping twice
    '''  
    try:        
        response = urllib2.urlopen('https://www.googleapis.com/customsearch/v1?key=%s&cx=008715276770992001381:iyfgiiccnki&q=%s&alt=atom&num=%d' % (appid['google'], urllib.quote(query), num))
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)            
        item_1 = soup.findAll('entry')[num-1]
        url =  ''.join(item_1.find('id').find(text=True))
        if single:
            desc = htmlx.unescape(htmlx.unescape(re.sub(r'&lt;[^&]+&gt;','',item_1.find('title').find(text=True))))
        else:
            desc = htmlx.unescape(htmlx.unescape(re.sub(r'&lt;[^&]+&gt;','',item_1.find('summary').find(text=True)))) 
        return ("%s, %s" % (url, desc)).encode('utf-8')
    except Exception:
        Log.error()
        return None

def googleimage(query, num=1, single=False):    
    '''
        @var query: Query for searching
        @var num: Get the nth result
        @var single: Get only the title 
        @summary: Performs a Google search on thinkdigit forum and returns the result
    '''    
    try:        
        response = urllib2.urlopen('https://www.googleapis.com/customsearch/v1?key=%s&cx=008715276770992001381:iyfgiiccnki&q=%s&alt=atom&num=%d&searchType=image' % (appid['google'], urllib.quote(query), num))
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)            
        item_1 = soup.findAll('entry')[num-1]
        url =  ''.join(item_1.find('id').find(text=True))
        if single:
            desc = htmlx.unescape(htmlx.unescape(re.sub(r'&lt;[^&]+&gt;','',item_1.find('title').find(text=True))))
        else:
            desc = htmlx.unescape(htmlx.unescape(re.sub(r'&lt;[^&]+&gt;','',item_1.find('summary').find(text=True)))) 
        return ("%s, %s" % (url, desc)).encode('utf-8')
    except Exception:
        Log.error()
        return None
        
def tdf(query, num=1, single=False):    
    '''
        @var query: Query for searching
        @var num: Get the nth result
        @var single: Get only the title 
        @summary: Performs a Google search on thinkdigit forum and returns the result
    '''  
    return customsearch(query, 'thinkdigit.com/forum/', num, single)

def youtube(query, num=1, single=False):    
    '''
        @var query: Query for searching
        @var num: Get the nth result
        @var single: Get only the title 
        @summary: Performs a Google search on thinkdigit forum and returns the result
    '''  
    return customsearch(query, 'youtube.com', num, single)

def imdb(query, num=1, single=False):    
    '''
        @var query: Query for searching
        @var num: Get the nth result
        @var single: Get only the title 
        @summary: Performs a Google search on thinkdigit forum and returns the result
    '''  
    return customsearch(query, 'imdb.com', num, single)

def customsearch(query, site, num=1, single=False):    
    '''
        @var query: Query for searching
        @var site : The site to search
        @var num: Get the nth result
        @var single: Get only the title        
        @summary: Performs a Google search on a site and returns the nth result
    '''  
    try:        
        response = urllib2.urlopen('https://www.googleapis.com/customsearch/v1?key=%s&cx=008715276770992001381:iyfgiiccnki&q=%s&alt=atom&num=1&siteSearch=%s' % (appid['google'], urllib.quote(query), site))        
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)            
        item_1 = soup.findAll('entry')[num-1]
        url =  ''.join(item_1.find('id').find(text=True))
        title = htmlx.unescape(htmlx.unescape(re.sub(r'&lt;[^&]+&gt;','',item_1.find('title').find(text=True))))   
        if not single:         
            desc = ", " + htmlx.unescape(htmlx.unescape(re.sub(r'&lt;[^&]+&gt;','',item_1.find('summary').find(text=True))))
        else:
            desc = ''
        return ("%s : %s%s" % (title, url, desc)).encode('utf-8')
    except Exception:
        Log.error()
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
    except Exception:
        Log.error()
        return None        