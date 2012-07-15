'''
Created on Jun 30, 2012

@author: Nisheeth
'''
import sqlite3

class SqliteDb(object):
    '''
        classdocs
    '''
    
    def __init__(self, dbname=None):
        '''
        Constructor
        '''
        if dbname is None:
            dbname = 'qirc.db'
        self._connection = sqlite3.connect(dbname, check_same_thread=False)
        self._cursor = self._connection.cursor()
    
    def reset_cursor(self):        
        self._cursor.close()
        self._cursor = self._connection.cursor()
        
    def select_query(self, query, args):
        result = self._cursor.execute(query, args)
        return (result, self._cursor.rowcount, -1, self._cursor.description)
    
    def update_query(self, query, args):
        result = self._cursor.execute(query, args)
        self._connection.commit()
        return (result, self._cursor.rowcount, self._cursor.lastrowid, self._cursor.description)
        
    def close(self):
        self._cursor.close()
        self._connection.close()