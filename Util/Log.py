'''
Created on Jun 10, 2012

@author: Nisheeth
'''

from Queue import Queue
from Queue import Empty
import time
import os
import traceback
from threading import Thread

# Patch functions of traceback for single line error reporting

def format_list(extracted_list):
    """Format a list of traceback entry tuples for printing.

    Given a list of tuples as returned by extract_tb() or
    extract_stack(), return a list of strings ready for printing.
    Each string in the resulting list corresponds to the item with the
    same index in the argument list.  Each string ends in a newline;
    the strings may contain internal newlines as well, for those items
    whose source text line is not None.
    """   
    l = []
    for filename, lineno, name, _ in extracted_list:
        item = '%s, %s:%d -> ' % (filename,name,lineno)        
        l.append(item)
    return l    

def format_exception(etype, value, tb, limit = None):
    """Format a stack trace and the exception information.

    The arguments have the same meaning as the corresponding arguments
    to print_exception().  The return value is a list of strings, each
    ending in a newline and some containing internal newlines.  When
    these lines are concatenated and printed, exactly the same text is
    printed as does print_exception().
    """
    if tb:
        l = []
        l = l + traceback.format_tb(tb, limit)
    else:
        l = []
    l = l + traceback.format_exception_only(etype, value)
    return l

# Assign functions
traceback.format_list = format_list
traceback.format_exception = format_exception

# Logging Module
class Log(object):
    '''
        Enables a LogCat like static logging class for Qirc
    '''
    _filename = 'Qirc.log'
    
    _queue = Queue()
    _stop = False
    _thread = None
    timestamps = False
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
                    print '%s%s %s' % (time.strftime('[%d-%m-%Y %H:%M:%S] ') if cls.timestamps else '', mode, str(msg))
                        
                if cls._thread is None:
                    cls._thread = Thread(target=Log.perform_write, name='perform_write')
                    cls._thread.start()
                try:                        
                    cls._queue.put('%s%s %s\n' % (time.strftime('[%d-%m-%Y %H:%M:%S] ') if cls.timestamps else '', mode, str(msg)))
                except Exception, e:
                    print '>> Log.write %s' % e
                    
            except Exception, e:
                print '> Log.write %s' %e
    
    @classmethod
    def error(cls, msg=''):          
        cls.write('%s%s' % (msg, traceback.format_exc(1)), 'E') 
                        
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
        