'''
Created on Jun 9, 2012
@author: Nisheeth
'''

import urllib2
import urllib
import hashlib
import cookielib
from Util.Log import Log
from Util import htmlx

class CleverBot(object):
    '''
        CleverBot handles the interaction between the bot by replying using cleverbot.com 
    '''
    def __init__(self, params=None):
        self.params = {
                    'url'       : 'http://www.cleverbot.com/webservicemin'
                }
        if params:
            self.params.update(params)
            
        self.data = {
                 'stimulus'         : '',
                 'start'            : '',
                 'sessionid'        : '',
                 'vText8'           : '',
                 'vText7'           : '',
                 'vText6'           : '',
                 'vText5'           : '',
                 'vText4'           : '',
                 'vText3'           : '',
                 'vText2'           : '',
                 'icognoid'         : 'wsf',
                 'icognocheck'      : '',
                 'fno'              : '0',
                 'prevref'          : '',
                 'emotionaloutput'  : '',
                 'emotionalhistory' : '',
                 'asbotname'        : 'Mystiq',
                 'ttsvoice'         : '',
                 'typing'           : '',
                 'lineref'          : '',                 
                 'sub'              : 'Say',
                 'islearning'       : '1',
                 'cleanslate'       : 'false'
            }
        self.headers = {
                    'User-Agent'        : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:7.0.1) Gecko/20100101 Firefox/7.0',
                    'Accept'            : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language'   : 'en-us;q=0.8,en;q=0.5',
                    'X-Moz'             : 'prefetch',
                    'Accept-Charset'    : 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                    'Referer'           : 'http://www.cleverbot.com',
                    'Cache-Control'     : 'no-cache',
                    'Pragma'            : 'no-cache'
                }
        self.response_keys = [
                      'message',
                      'sessionid',
                      'logurl',
                      'vText8',
                      'vText7',
                      'vText6',
                      'vText5',
                      'vText4',
                      'vText3',
                      'vText2',
                      'prevref',
                      '__unused__',
                      'emotionalhistory',
                      'ttsLocMP3',
                      'ttsLocTXT',
                      'ttsLocTXT3',
                      'ttsText',
                      'lineref',
                      'lineURL',
                      'linePOST',
                      'lineChoices',
                      'lineChoicesAbbrev',
                      'typingData',
                      'divert',
                ]
        self.response = {}
        self.connect()
    
    def connect(self):
        cj = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
                
    def ask(self, msg):
        try:
            self.data['stimulus'] = msg        
            self.data['icognocheck'] = self.query_hash(self.data)            
            req = urllib2.Request(self.params['url'], urllib.urlencode(self.data), self.headers)
            resp = self.opener.open(req)
            msg = resp.read()
            resp.close()
            return self.parse_response(msg)
        except Exception:
            Log.error()
            return None                    
                
    def parse_response(self, resp):                       
        for k,v in zip(self.response_keys, resp.split("\r")):
            try:
                self.response[k] = v
                if self.data.has_key(k):
                    self.data[k] = v
            except:
                pass
        return htmlx.unescape(self.response['ttsText'])
        
    def query_hash(self, params):
        query = urllib.urlencode(params)[9:29]
        return hashlib.md5(query).hexdigest()
        