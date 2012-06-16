'''
Created on Jun 10, 2012

@author: Nisheeth
'''

from Queue import Queue
from Queue import Empty
import time
import os
from threading import Thread

class Log(object):
    '''
    classdocs
    '''
    _filename = 'Qirc.log'
    _timestamps = False
    _queue = Queue()
    _stop = False
    _thread = None
    debug = False
    enabled = True
                 
    @classmethod
    def purge(cls):
        in_use = True
        while in_use and os.path.isfile(cls._filename):
            try:
                os.remove(cls._filename)
                in_use = False
            except Exception, e:
                print 'Log.purge', e
                pass
            
       
    @classmethod
    def write(cls, msg, mode=None):
        if cls.enabled:
            try:
                if not mode:
                    mode = 'N'
                
                if cls.debug:
                    print '%s %s' % (mode, str(msg))
                else:        
                    if cls._thread is None:
                        cls._thread = Thread(target=Log.perform_write, name='perform_write')
                        cls._thread.start()
                    try:                        
                        cls._queue.put('%s%s %s\n' % (time.strftime('%d-%m-%Y %H:%M:%S ') if cls._timestamps else '', mode, str(msg)))
                    except Exception, e:
                        print '>> Log.write %s' % e
                    
            except Exception, e:
                print '> Log.write %s' %e
        
    @classmethod    
    def perform_write(cls):        
        while not cls._stop:                   
            try:            
                item = cls._queue.get(True, 10)
                cls.write_file(item)
                cls._queue.task_done()
            except Empty:
                pass
            except Exception, e:
                print 'Log.perform_write', e                  
                pass
    
    @classmethod
    def write_file(cls, data):
        retry = True
        while retry:
            try:
                with open(cls._filename, 'a') as f:
                    f.write(data)                
                retry = False
            except Exception, e:
                retry = True
                print 'Log.write_file', e
                pass  
                
    @classmethod
    def stop(cls):
        cls._stop = True
        