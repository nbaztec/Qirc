'''
Created on Jun 30, 2012

@author: Nisheeth
'''

import socket
import urllib
import urllib2
import json
import re
from Util.Log import Log
from Util.BeautifulSoup import BeautifulSoup
from Util.Config import ConfigManager
from Util import htmlx

config = ConfigManager.read_config('extensions.conf', 'google')
#config = {
#            'google'    : 'AIzaSyAMajmwMaD4uPv1EuXn_WzC-9T61GZW5gw',
#        }

url_regex = re.compile(r'^https?://([^/]+)(.*)$')

def min_url(url, maxlen=20):
    idx = url.find('://')
    if idx != -1:
        url = url[idx+3:]
    if len(url) > maxlen:
        url = url[:maxlen/2] + '...' + url[-maxlen/2:]
    return url

def dns(url):
    '''
        @param url: The url to resolve
        @summary: Performs the DNS lookup of host        
    '''
    try:
        host = url_regex.match(url).group(1)
        return '%s resolved to %s' % (host, socket.getaddrinfo(host, 80)[0][4][0])
    except:
        return None

def port(url, port):
    '''
        @param url: The url to resolve
        @param port: The port to connect to
        @summary: Checks if the specified port is open on the server
    '''    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        host = url_regex.match(url).group(1)
        s.connect((host, port))
        s.shutdown(2)
        return 'Port %d is open on %s' % (port, host)
    except:
        return None       
    
def visit(url):
    '''
        @param url: The url to resolve
        @summary: Visits the url and gets the information about it
        @return: (status code, content type, final url) 
    '''
    try:        
        status = None
        ctype = None        
        request = urllib2.Request(url)        
        request.get_method = lambda: 'HEAD'
        try:
            response = urllib2.urlopen(request)
            status = response.getcode()
            ctype = response.info().getheader('content-type')
        except urllib2.URLError, e:            
            if e.code in (301, 302, 303, 307):      # Redirection loop
                status = 302
            else:
                status = e.code        
        return status, ctype, url
    except Exception:            
        Log.error('URL.visit: ')        
        return None, None, None
 
def title(url, only_title=False):
    '''
        @param url: The url to resolve
        @summary: Fetches the title of an url 
    '''
    status, ctype, url = visit(url)
    if url is None:
        return None
    else:
        if status == 302:
            return 'Redirection loop detected for url %s' % url
        elif status == 200:        
            try:
                if ctype.startswith('text/'):
                    # Fast Title Search
                    found = None
                    buff = ''
                    m = 0
                    n = 512     # Chunk Size
                    while True:
                        req = urllib2.Request(url)
                        req.headers['Range'] =  'bytes=%s-%s' % (m, m+n-1)
                        response = urllib2.urlopen(req)    
                        buff += response.read()                        
                        response.close()
                        soup = BeautifulSoup(buff)
                        found = soup.find('title')
                        m += n
                        # If PARTIAL OK (206) and <title> has an ending tag
                        if response.code == 200 or (response.code == 206 and found and found.nextSibling):
                            break
                    if only_title:      
                        return 'Title: %s' % htmlx.unescape(u''.join(found.findAll(text=True))).encode('utf-8')
                    else:
                        return '%s : [%s]' % (htmlx.unescape(u''.join(found.findAll(text=True))).encode('utf-8'), min_url(url))
                else:                    
                    return 'Title not available for content type %s : url %s' % (ctype, min_url(url))
            except Exception:
                Log.error()
                return None
        else:
            return 'Status Code %s : url %s' % (status, url)  

def content_type(url):
    '''
        @param url: The url to resolve
        @summary: Fetches the content type of an url 
    '''
    status, ctype, url = visit(url)
    if url is None:
        return None
    else:
        if status == 302:
            return 'Redirection loop detected for url %s' % url        
        elif status == 200:
            return 'Content type %s : [%s]' % (ctype, min_url(url))
        else:
            return 'Status Code %s : [%s]' % (status, min_url(url))

def description(url):
    '''
        @param url: The url to resolve
        @summary: Fetches the meta-description of an url 
    '''
    status, ctype, url = visit(url)
    if url is None:
        return None
    else:
        if status == 302:
            return 'Redirection loop detected for url %s' % url
        elif status == 200:        
            try:
                if ctype.startswith('text/'):
                    response = urllib2.urlopen(url)        
                    page = response.read()                        
                    response.close()
                    soup = BeautifulSoup(page)
                    desc = soup.find('meta', {'name': re.compile('description', re.I)})['content']                    
                    return 'Description %s : [%s]' % (htmlx.unescape(desc), min_url(url))
                else:
                    return 'Preview not available for content type %s : [%s]' % (ctype, min_url(url))
            except Exception:
                Log.error()
                return None
        else:
            return 'Status Code %s : url %s' % (status, url)  

def googleshort(url):
    '''
        @param url: The url to shorten
        @summary: Shortens the url to its the goo.gl url 
    '''    
    try:
        req = urllib2.Request('https://www.googleapis.com/urlshortener/v1/url?key=%s' % config['app-id'], data='{"longUrl": "%s"}' % url, headers={'Content-Type': 'application/json'})
        response = urllib2.urlopen(req)        
        page = response.read()                        
        response.close()
        result = json.loads(page)        
        return 'Short URL %s : %s' % (result['id'], min_url(result['longUrl']))
    except Exception:
        Log.error()
        return None

def googleexpand(url):
    '''
        @param url: The url to shorten
        @summary: Gets the full url of a goo.gl url 
    '''
    try:        
        response = urllib2.urlopen('https://www.googleapis.com/urlshortener/v1/url?key=%s&shortUrl=%s' % (config['app-id'], urllib.quote(url)))        
        page = response.read()                        
        response.close()
        result = json.loads(page)    
        if result['status'] == 'OK':
            return 'Expanded URL %s : %s' % (result['id'], result['longUrl'])
        else:
            return None
    except Exception:
        Log.error()
        return None
