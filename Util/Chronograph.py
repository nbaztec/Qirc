'''
Created on Sep 15, 2012

@author: Nisheeth
'''
from datetime import datetime

def time_ago(timestamp, milliseconds=False, resolution=2):
    '''
        @param timestamp: The datetime to compare against
        @summary: Returns a string signifying the elapsed time 
    '''
    d = datetime.utcnow() - timestamp  + datetime(1, 1, 1)  # Add dummy date: 1y-1m-1d, to form a datetime object 
    s = ''
        
    if d.year-1:
        s += str(d.year-1)+'y '
    if d.month-1:
        s += str(d.month-1)+'m '    
    if d.day-1:
        s += str(d.day-1)+'d '
    if d.hour:
        s += str(d.hour)+'h '
    if d.minute:
        s += str(d.minute)+'m '
    if d.second:        
        s += str(d.second + (round(d.microsecond/1000000.0, resolution) if milliseconds else 0))+'s '
    return s.rstrip()