'''
Created on Jan 12, 2013
@author: Nisheeth Barthwal
@author: Anurag Panda
@summary: Posts IRC message at twitter
'''

import urllib
import urllib2
import json
from Util import OAuth
from Util.Config import ConfigManager

config = ConfigManager.read_config('extensions.conf', 'twitter')

oauth_consumer = OAuth.OAuthConsumer(key=config['consumer-key'], secret=config['consumer-secret'])
oauth_token = OAuth.OAuthToken(key=config['access-key'], secret=config['access-secret'])
    
def twitter_api_send(method, url, data, oa_consumer, oa_token=None):
    '''
        @param method: POST or GET
        @param url: The url to request against
        @param data: dict of data to send
        @param oa_consumer: Instance of OAuthConsumer
        @param oa_token: Instance of OAuthToken
    '''
    headers = {}
    request = OAuth.OAuthRequest.from_consumer_and_token(oa_consumer, token=oa_token, http_url=url, http_method=method, parameters=data)
    request.sign_request(OAuth.OAuthSignatureMethod_HMAC_SHA1(), oa_consumer, oa_token)
    headers['Accept'] = '*/*'
    headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11'
    headers['Content-Type'] = 'application/x-www-form-urlencoded'    
    
    headers.update(request.to_header(url))    
        
    
    if data:
        data = urllib.urlencode(data.items())
        
    req = urllib2.Request(url, data, headers=headers)    
    req.get_method = lambda: method    
    
    try:
        d = json.loads(urllib2.urlopen(req).read())
        if d.has_key('errors'):
            return False, 'Error (%d): %s' % (d['errors'][0]['code'], d['errors'][0]['message'])
        else:            
            return True, d['user']['screen_name']
    except Exception, e:
        d = json.loads(e.read())        
        return False, 'Error (%d): %s' % (d['errors'][0]['code'], d['errors'][0]['message'])
        
def tweet(status):    
    r, msg = twitter_api_send('POST', 'https://api.twitter.com/1.1/statuses/update.json', {'status': status}, oauth_consumer, oauth_token)
    if r:
        return 'Tweeted by @%s' % msg
    else:
        return msg