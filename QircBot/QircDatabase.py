'''
Created on Jun 30, 2012

@author: Nisheeth
'''
import sqlite3
import os

class SqliteDb(object):
    '''
        Wraps a sqlite database for Qirc
    '''
    
    def __init__(self, dbname=None):
        if dbname is None:
            dbname = 'qirc.db'
        
        create = not os.path.exists(dbname)
            
        self._connection = sqlite3.connect(dbname, check_same_thread=False)
        self._cursor = self._connection.cursor()
        
        if create:
            self.create()
    
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
        self._cursor.execute("""CREATE TABLE IF NOT EXISTS users(
                id integer PRIMARY KEY NOT NULL,
                nick text NOT NULL, 
                ident text NOT NULL, 
                host text NOT NULL,
                UNIQUE(nick, ident, host)
            )""")
        
        self._cursor.execute("""CREATE TABLE IF NOT EXISTS aliases(
                uid integer NOT NULL,                
                nick text NOT NULL, 
                ident text NOT NULL, 
                host text NOT NULL,
                num_joins integer NOT NULL DEFAULT 1,
                timestamp datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(uid) REFERENCES users(id),
                UNIQUE(uid, nick, ident, host)
            )""")
        
        self._cursor.execute("""CREATE TABLE IF NOT EXISTS user_channels(
                uid integer NOT NULL,
                channel text NOT NULL,
                num_joins integer NOT NULL DEFAULT 1,
                timestamp datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                quit_reason,
                FOREIGN KEY(uid) REFERENCES users(id),
                UNIQUE(uid, channel)
            )""")
        
    def clear(self):
        self.update_query('DELETE FROM aliases WHERE 1',())
        self.update_query('DELETE FROM users WHERE 1',())
        
    def drop(self):
        self.update_query('DROP TABLE aliases',())
        self.update_query('DROP TABLE users',())