'''
Created on Jun 30, 2012

@author: Nisheeth
'''
import sqlite3

class SqliteDb(object):
    '''
        Wraps a sqlite database for Qirc
    '''
    
    def __init__(self, dbname=None):
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
        
    def create(self):        
        self._cursor.execute("""CREATE TABLE users(
                id integer PRIMARY KEY NOT NULL,
                nick text NOT NULL, 
                ident text NOT NULL, 
                host text NOT NULL,
                num_joins integer NOT NULL DEFAULT 1,
                timestamp datetime NOT NULL DEFAULT CURRENT_TIMESTAMP, 
                quit_reason, 
                UNIQUE(nick, ident, host)
            )""")
        
    def clear(self):
        self.update_query('DELETE FROM users WHERE 1',())