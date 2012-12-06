'''
Created on Jun 8, 2012
@author: Nisheeth
@summary: Provides provision for location tracking
'''

import urllib
import urllib2
from Util.BeautifulSoup import BeautifulSoup
from Util.Log import Log

appid = {
            'ipinfo'    : ''
        }
   
def iplocate(ip): 
    '''
        @param ip: The IP address
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
    except Exception:
        Log.error()
        return None
        
def geo(latitude, longitude): 
    '''
        @param latitude: The latitude of location
        @param longitude: The longitude of location
        @summary: Performs a reverse geo lookup on Google Maps API
    '''     
    try:
        response = urllib2.urlopen('http://maps.googleapis.com/maps/api/geocode/xml?latlng=%s,%s&sensor=false' % (latitude, longitude))        
        page = response.read()                            
        response.close()
        soup = BeautifulSoup(page)
        for addr in soup.findAll('formatted_address'):
            address = addr.find(text=True)
            if address:
                address = str(address)
                break       
        return '[%s, %s] : %s' % (latitude, longitude, address)        
    except Exception:
        Log.error()
        return None