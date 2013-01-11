'''
Created on Jun 23, 2012
author: Nisheeth
'''

from datetime import timedelta
import time
import re
from threading import Thread, Condition


class SimpleError(Exception):
    def __init__(self, msg):
        self.message = msg
        
    def __str__(self):
        return "Error", self.message

class TimeFormatError(SimpleError):
        def __init__(self, msg):
            super(TimeFormatError, self).__init__(msg) 
    
class TimeValueError(SimpleError):
    def __init__(self, msg):
        super(TimeValueError, self).__init__(msg)
        
class Timer(object):
    '''
    Triggers an action after a particular time
    '''
    def __init__(self, buff=None):
        if buff is None:
            buff = []
        self._buffer = buff
        self.__close = False
        self._cv_exit = Condition()
        self._regex_parse = re.compile(r'^(\d+)(d|h|m|s)$', re.I)
        Thread(target=self.timer, name='timer_thread').start()
        
    
    def clear(self):
        count = len(self._buffer)        
        self._buffer = []
        return count
        
    def dispose(self):
        self.__close = True
        self._cv_exit.acquire()
        self._cv_exit.notify_all()
        self._cv_exit.release()
        
    def timer(self):
        '''                    
            @summary: Polls the timer
        '''
        while not self.__close:            
            self._cv_exit.acquire()
            self._cv_exit.wait(15)
            self._cv_exit.release()
            now = int(time.time())
            for k, v in self._buffer:                
                if k <= now:
                    for method, args in v:
                        try:
                            method(*args)
                        except:
                            pass
                    self._buffer.remove((k,v))
                else:
                    break
                    
    def parse_time(self, text):
        '''
            @param text: The time string received
            @summary: Parses the text to create a time 
        '''
        
        # Fix for py2.6 not having td.total_seconds()
        def _total_seconds(td):
            return td.microseconds + (td.seconds + td.days * 24 * 3600)
        
        m = self._regex_parse.match(text)
        if m is not None:
            try:
                rel = int(m.group(1))
            except:
                raise TimeFormatError("Invalid value format")
                        
            if m.group(2) == 'd':
                return int(time.time() + _total_seconds(timedelta(days=rel)))
            elif m.group(2) == 'h':
                return int(time.time() + _total_seconds(timedelta(hours=rel)))
            elif m.group(2) == 'm':
                return int(time.time() + _total_seconds(timedelta(minutes=rel)))
            elif m.group(2) == 's':
                return int(time.time() + _total_seconds(timedelta(seconds=rel)))
        raise TimeFormatError("Invalid value format")
        
    def register(self, time, method, args, parse=True):
        '''
            @param time: The timestamp to remind on
            @param method: The method to call
            @param args: args to pass the method
            @summary: Puts the tuple (timstamp, [(channel, method, args)] in a list 
        '''
        if parse:
            time = self.parse_time(time)
        
        idx = 0     

        for i in range(0, len(self._buffer)):
            if self._buffer[i][0] == time:
                self._buffer[i][1].append((method, args))
                idx = -1
            elif self._buffer[i][0] > time:
                idx = i                               
                break
            else:
                idx = i + 1 

        if idx != -1:
            self._buffer.insert(idx, (time, [(method, args)]))   