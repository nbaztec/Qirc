'''
Created on Jun 23, 2012
author: Nisheeth
'''

class UserMessage(object):
    '''
    UserMessage acts as a buffer to hold messages for user and retrieves them at once
    '''
    def __init__(self):
        self._buffer = {}
        
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
            
        
            
        
            
        