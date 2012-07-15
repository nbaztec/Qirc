'''
Created on Jun 9, 2012
@author: Nisheeth
'''

from threading import Thread
import time

class VoteMaster(object):
    '''
        @summary: A generic class to manage voting sessions
    '''
    def __init__(self):               
        self.is_voting = False
        self._result = None
        self._output = None
        
    def start(self, time, ques, output, result):
        '''
            @var ques: The voting question
            @summary: Starts a voting session
        '''
        if self.is_voting:      # Don't start if existing session is underway
            return None
        
        self._result = result
        self._output = output
        self._time = time
        self.ques = ques        
        self.users = []
        self.votep = 0
        self.voten = 0
        Thread(target=self.voting_period, name='voting_period').start()         # Start timer
        if self._output:
            Thread(target=self._output, args=("Voting started (%ds) for: '%s', Vote + or -" % (time, ques),), name='VoteMaster._output').start()
        return True
            
        
    def register_vote(self, nick, host, vote):
        '''
            @var nick: The nick of user who voted
            @var host: The host of user who voted
            @var vote: The vote (+,-)
            @summary: Registers a unique vote per user
            @notice: Host is used to identify same people            
        '''
        if host not in self.users:              # Register 1 vote per user
            if vote == '+':
                self.votep += 1
                self.users.append(host)
            elif vote == '-':
                self.voten += 1
                self.users.append(host)
            elif self._output:
                Thread(target=self._output, args=('Only +/- are valid %s. Revote' % nick,), name='VoteMaster._output').start()      
    
    def voting_period(self):
        '''            
            @summary: Calls the timeout of voting period
        '''        
        self.is_voting = True
        time.sleep(self._time)                          # 10 second time for vote
        self.is_voting = False
        self.result()
        
    def result(self):
        '''            
            @summary: Returns the outcome of the voting session
        '''
        if self._result:                
            Thread(target=self._result, args=(self.votep, self.voten, self.ques, ), name='VoteMaster._result').start()    
        