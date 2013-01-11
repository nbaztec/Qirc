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
        self._result = None
        self._output = None
        self._vote = {}
        
    def start(self, channel, time, ques, output, result):
        '''
            @param ques: The voting question
            @summary: Starts a voting session
        '''
        if channel in self._vote.keys():      # Don't start if existing session is underway
            return None
        
        self._result = result
        self._output = output
        
        self._vote[channel] = {
                                'time'  : max(5, time),                               
                                'ques'  : ques,
                                'users' : [],
                                'vote+' : 0,
                                'vote-' :0
                              }
        
        Thread(target=self.voting_period, args=(channel,), name='voting_period').start()         # Start timer
        if self._output:
            Thread(target=self._output, args=(channel, "Voting started (%ds) for: '%s', Vote + or -" % (time, ques),), name='VoteMaster._output').start()
        return True
            
        
    def register_vote(self, channel, nick, host, vote):
        '''
            @param nick: The nick of user who voted
            @param host: The host of user who voted
            @param vote: The vote (+,-)
            @summary: Registers a unique vote per user
            @notice: Host is used to identify same people            
        '''
        if host not in self._vote[channel]['users']:              # Register 1 vote per user
            if vote == '+':
                self._vote[channel]['vote+'] += 1
                self._vote[channel]['users'].append(host)
            elif vote == '-':
                self._vote[channel]['vote-'] += 1
                self._vote[channel]['users'].append(host)
            elif self._output:
                Thread(target=self._output, args=(channel, 'Only +/- are valid %s. Revote' % nick,), name='VoteMaster._output').start()      
    
    def voting_period(self, channel):
        '''            
            @summary: Calls the timeout of voting period
        '''
        d = self._vote[channel]
        time.sleep(d['time'])                          # 10 second time for vote
        self._vote.pop(channel)
        self.result(channel, d['ques'], d['vote+'], d['vote-'])
        
    def result(self, channel, ques, votep, voten):
        '''            
            @summary: Returns the outcome of the voting session
        '''
        if self._result:                
            Thread(target=self._result, args=(channel, votep, voten, ques, ), name='VoteMaster._result').start()
            
    def is_voting(self, channel):
        return channel in self._vote.keys()
        