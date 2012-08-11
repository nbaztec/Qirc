'''
Created on Jun 23, 2012
author: Nisheeth
'''
from datetime import datetime
from datetime import timedelta
import time
import re
from threading import Thread

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
        
    def post(self, sender, to, text):
        '''
            @var sender: The nick of the sender
            @var to: The nick of the recepient
            @var text: The message to send
            @summary: Puts the tuple (sender, text) in the inbox of recepient 
        '''
        if self._buffer.has_key(to):
            self._buffer[to].append((sender, text))            
        else:
            self._buffer[to] = [(sender, text)]            
            
    def get(self, nick):
        '''
            @var nick: The nick of the recepient            
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
        Thread(target=self.timer, name='reminder_thread').start()
        
    def dispose(self):
        self.__close = True
        
    def parse_time(self, text):
        '''
            @var text: The time string received
            @summary: Parses the text to create a time 
        '''
        m = self._regex_parse.match(text)
        if m is not None:
            try:
                rel = int(m.group(1))
            except:
                raise self.RemindFormatError("Invalid value")
                        
            if m.group(2) == 'd':
                return int(time.time() + timedelta(days=rel).total_seconds())
            elif m.group(2) == 'h':
                return int(time.time() + timedelta(hours=rel).total_seconds())
            elif m.group(2) == 'm':
                return int(time.time() + timedelta(minutes=rel).total_seconds())
            elif m.group(2) == 's':
                if rel < 30:
                    raise self.RemindValueError("Value must be greater than 30 seconds")
                return int(time.time() + timedelta(seconds=rel).total_seconds())
        raise self.RemindFormatError("Invalid value")
        
    def remind(self, nick, time, text):
        '''
            @var time: The timestamp to remind on
            @var nick: The nick of the user            
            @var text: The message to remind
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
            time.sleep(15)
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
        
    def join(self, nick, ident, host):
        _,count,_,_ = self._qbsqlite.update_query('UPDATE `users` SET quit_reason=NULL, num_joins=num_joins+1, timestamp=CURRENT_TIMESTAMP WHERE nick=? AND ident=? AND host=?',(nick,ident,host,))
        if count == 0:
            self._qbsqlite.update_query('INSERT INTO `users`(nick,ident,host) VALUES(?,?,?)',(nick,ident,host,))
        
    def part(self, nick, reason):
        #self._qbsqlite.update_query('UPDATE `users` SET quit_reason=? WHERE nick=? AND ident=? AND host=?',(reason, nick,ident,host,))        
        self._qbsqlite.update_query('UPDATE users SET quit_reason=? WHERE id=(SELECT id FROM users WHERE nick=? ORDER BY timestamp DESC LIMIT 1)',(reason, nick,))
        
    def check(self, nick):
        r = self._qbsqlite.select_query('SELECT ident, host FROM users WHERE nick=? GROUP BY ident, host ORDER BY num_joins DESC',(nick,))[0].fetchone()
        if r is None:
            return None
        else:
            return self._qbsqlite.select_query('SELECT timestamp, quit_reason FROM users WHERE nick=? AND ident=? AND host=? ORDER BY timestamp DESC',(nick, r[0], r[1],))[0].fetchone()

    def seen(self, nick):
        r = self.check(nick)
        if r is None:
            return "No I haven't seen %s lately" % nick 
        elif r[0]:
            if r[1] is None:
                return '%s is right here' % nick
            else:         
                d = datetime.utcnow() - datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S') + datetime(1,1,1)
                s = ""        
                if d.day-1:
                    s += str(d.day-1)+'d '
                if d.hour:
                    s += str(d.hour)+'h '
                if d.minute:
                    s += str(d.minute)+'m '
                if d.second:
                    s += str(d.second)+'s '        
                return '%s was last seen: %sago (%s)' % (nick, s, r[1])