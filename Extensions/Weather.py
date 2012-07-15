'''
Created on Jun 8, 2012
@author: Nisheeth
@summary: Provides provisions for weather and forecasting
'''

import urllib
import urllib2
from Util.BeautifulSoup import BeautifulSoup
from Util.Log import Log


def to_celcius(f):
    return (float(f)-32)*5/9


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
    except Exception:
        Log.error()
        return None
    
def forecast(place, num=3): 
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
        for f in forecasts[:num]:
            r.append('%s on %s %dC-%dC' % (f.find('condition')['data'], f.find('day_of_week')['data'], to_celcius(f.find('low')['data']), to_celcius(f.find('high')['data'])))
        return ('%s: %s' % (soup.find('forecast_information').find('city')['data'], ' | '.join(r))).encode('utf-8')          
    except Exception:
        Log.error()
        return None