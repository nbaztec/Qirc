'''
Created on Jun 16, 2012
@author: Nisheeth
'''

from Queue import Queue
from threading import Thread

class ThreadQueue(object):
    '''
        ThreadQueue is a simple implementation for a reusable thread pool
    '''

    def __init__(self, maxsize=0):
        '''
        Constructor
        '''
        self._queue = Queue(maxsize)
        self._count = 0;
    
    @property       
    def Length(self): return self._count;
    
    def put(self, func, args=(), kwargs={}):
        '''
            @var func: The function
            @var args: The arguments
            @var kwargs: The keyworded arguments 
        '''
        self._queue.put((func, args, kwargs))
        self._count += 1
        
    def process(self):
        '''
            @summary: Processes all the functions in separate threads
        '''
        while self._count:
            Thread(target=self.worker, name='worker').start()
            self._count -= 1 
        
    def worker(self):
        '''
            @summary: Calls the target function with the set of arguments
        '''
        (func, args, kwargs) = self._queue.get()
        print func, args, kwargs
        try:        
            func(*args, **kwargs)
        finally:
            self._queue.task_done()
    
    def join(self):
        '''
            @summary: Block until all threads are finished
        '''
        self._queue.join()