'''
Created on Jan 12, 2013
@author: Anurag Panda
@summary: Posts IRC message at twitter
'''
from Util import OAuth
from Util.Config import ConfigManager

config = ConfigManager.read_config('extensions.conf', 'twitter')

def post(tweet):
    update_url = 'https://api.twitter.com/1.1/statuses/update.json'
    consumer_key = config['consumer-key']
    consumer_secret = config['consumer-secret']
    access_key = config['access-key']
    access_secret = config['access-secret']
    headers = None
    force_auth_header = False

    consumer = OAuth.Consumer(key=consumer_key, secret=consumer_secret)
    token = OAuth.Token(key=access_key, secret=access_secret)

    client = OAuth.Client(consumer, token)

    resp, content = client.request(update_url, 'POST', 'status=%s'%tweet, headers, force_auth_header)

    if resp['status'] == '200':
        return 'Tweet posted'
    else:
        return 'Tweet posting failed. Did you duplicate your tweet too quickly?'
