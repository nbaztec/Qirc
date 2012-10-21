'''
Created on Jun 23, 2012
author: Nisheeth
'''
from datetime import datetime
from datetime import timedelta
import time
import re
from threading import Thread, Condition


class SimpleError(Exception):
    def __init__(self, msg):
        self.message = msg
        
    def __str__(self):
        return "Remind Error", self.message
    
class Tell(object):
    '''
    Tell acts as a buffer to hold messages for user and retrieves them at once
    '''
    def __init__(self, buff=None):
        if buff is None:
            buff = {}
        self._buffer = buff
    
    def clear(self):
        count = len(self._buffer)
        self._buffer = {}
        return count
        
    def post(self, sender, to, text):
        '''
            @param sender: The nick of the sender
            @param to: The nick of the recepient
            @param text: The message to send
            @summary: Puts the tuple (sender, text) in the inbox of recepient 
        '''
        if self._buffer.has_key(to):
            self._buffer[to].append((sender, text, datetime.utcnow()))            
        else:
            self._buffer[to] = [(sender, text, datetime.utcnow())]
            
    def get(self, nick):
        '''
            @param nick: The nick of the recepient            
            @summary: Gets the list of tuples (sender, text) in the inbox of recepient
            @return: [(sender,text), (sender,text), ...]
        '''
        return self._buffer.pop(nick, None)
    
    def get_state(self):
        return {'buffer': self._buffer}
    
    def set_state(self, state):
        self._buffer = state['buffer']
                                 
class Remind(object):
    '''
        Keeps a reminder for a user and delivers it on time
    '''
    
    class RemindFormatError(SimpleError):
        def __init__(self, msg):
            SimpleError.__init__(self, msg) 
    
    class RemindValueError(SimpleError):
        def __init__(self, msg):
            SimpleError.__init__(self, msg) 
        
    def __init__(self, print_callback, buff=None):
        if buff is None:
            buff = []
        self._buffer = buff
        self._print = print_callback
        self._regex_parse = re.compile(r'^(\d+)(d|h|m|s)$', re.I)
        self.__close = False
        self._cv_exit = Condition()
        Thread(target=self.timer, name='reminder_thread').start()
        
    def clear(self):
        count = len(self._buffer)
        self._buffer = []
        return count
        
    def dispose(self):
        self.__close = True
        self._cv_exit.acquire()
        self._cv_exit.notify_all()
        self._cv_exit.release()
        
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
                raise self.RemindFormatError("Invalid value")
                        
            if m.group(2) == 'd':
                return int(time.time() + _total_seconds(timedelta(days=rel)))
            elif m.group(2) == 'h':
                return int(time.time() + _total_seconds(timedelta(hours=rel)))
            elif m.group(2) == 'm':
                return int(time.time() + _total_seconds(timedelta(minutes=rel)))
            elif m.group(2) == 's':
                if rel < 30:
                    raise self.RemindValueError("Value must be greater than 30 seconds")
                return int(time.time() + _total_seconds(timedelta(seconds=rel)))
        raise self.RemindFormatError("Invalid value")
        
    def remind(self, nick, time, text):
        '''
            @param time: The timestamp to remind on
            @param nick: The nick of the user            
            @param text: The message to remind
            @summary: Puts the tuple (timstamp, [(sender, text)] in a list 
        '''        
        time = self.parse_time(time)   
        idx = 0     
        for i in range(0, len(self._buffer)):            
            if self._buffer[i][0] == time:
                self._buffer[i][1].append((nick, text))
                idx = -1
            elif self._buffer[i][0] > time:
                idx = i                               
                break
            else:
                idx = i + 1 

        if idx != -1:
            self._buffer.insert(idx, (time, [(nick, text)]))              
        
    def timer(self):
        '''                    
            @summary: Polls the reminder list
        '''
        while not self.__close:            
            self._cv_exit.acquire()
            self._cv_exit.wait(15)
            self._cv_exit.release()
            now = int(time.time())
            for k,v in self._buffer:
                if k <= now:
                    for u, m in v:
                        self._print("Reminder for %s, '%s'" % (u, m))
                    self._buffer.remove((k,v))
                else:
                    break
        
    def get_state(self):
        return {'buffer': self._buffer}
    
    def set_state(self, state):
        self._buffer = state['buffer']
        
class Seen(object):
    '''
    Tell acts as a buffer to hold messages for user and retrieves them at once
    '''
    def __init__(self, qbsqlite):
        self._qbsqlite = qbsqlite
        
    def init(self, names):
        for name in names.values():
            if name.nick:
                self.join(name.nick, name.ident, name.host, 0)
                
    def join(self, nick, ident, host, inc=1):
        _,count,rid,_ = self._qbsqlite.update_query('UPDATE `users` SET quit_reason=NULL, num_joins=num_joins+?, timestamp=CURRENT_TIMESTAMP, nick=?, ident=? WHERE host=?',(inc, nick,ident,host,))
        if count:
            r = self._qbsqlite.select_query('SELECT id FROM `users` WHERE host=?',(host,))[0].fetchone()
            if r:
                _,count,_,_ = self._qbsqlite.update_query('UPDATE `aliases` SET num_joins=num_joins+?, timestamp=CURRENT_TIMESTAMP WHERE uid=? AND nick=? AND ident=?',(inc, r[0], nick,ident,))
                if count == 0:                    
                    self._qbsqlite.update_query('INSERT INTO `aliases`(uid,nick,ident,host,num_joins) VALUES(?,?,?,?,?)',(r[0], nick,ident,host,1,))
        else:        
            _,_,rid,_ = self._qbsqlite.update_query('INSERT INTO `users`(nick,ident,host,num_joins) VALUES(?,?,?,?)',(nick,ident,host,1,))
            self._qbsqlite.update_query('INSERT INTO `aliases`(uid,nick,ident,host,num_joins) VALUES(?,?,?,?,?)',(rid, nick,ident,host,1,))
        
    def part(self, nick, ident, host, reason):                
        self._qbsqlite.update_query('UPDATE users SET timestamp=CURRENT_TIMESTAMP, quit_reason=? WHERE host=?',(reason, host,))
        
    def seen(self, nick):
        r = self._qbsqlite.select_query('SELECT uid FROM aliases WHERE nick=? ORDER BY num_joins DESC, timestamp DESC LIMIT 1',(nick,))[0].fetchone()
        if r is None:
            return None, None, None, None
        else:
            res, _, _, _, = self._qbsqlite.select_query('SELECT nick, ident, host FROM aliases WHERE uid=? ORDER BY num_joins DESC, timestamp DESC',(r[0],))            
            nicks = []
            for c in res:                
                nicks.append(c[0])
            r = self._qbsqlite.select_query('SELECT ident, host, timestamp, quit_reason FROM users WHERE id=? ORDER BY timestamp DESC LIMIT 1',(r[0], ))[0].fetchone()
            if r:
                return nicks, ('%s!%s@%s' % (nick, r[0], r[1])), r[2], r[3]
            else:
                return None, None, None, None