'''
Created on Jun 9, 2012

@author: Nisheeth
'''

from threading import Thread
import time

class VoteManager(object):
    
    def __init__(self, callback):        
        self.callback = callback        
        self.is_voting = False
    
    def start(self, ques):
        if self.is_voting:
            return None
        
        self.ques = ques        
        self.users = []
        self.votep = 0
        self.voten = 0
        Thread(target=self.voting_period, name='voting_period').start()
        return "Voting started (10s) for: '%s', Vote + or -" % ques
        
    def got_vote(self, user, vote):
        if user not in self.users:            
            if vote == '+':
                self.votep += 1
                self.users.append(user)
            elif vote == '-':
                self.voten += 1
                self.users.append(user)
            else:
                Thread(target=self.callback, args=('Only +/- are valid %s. Revote' % user, )).start()      
    
    def voting_period(self):
        self.is_voting = True
        time.sleep(10)
        self.is_voting = False
        self.result()
        
    def result(self):
        self.vote = self.votep - self.voten
        print self.vote, self.votep, self.voten
        if self.vote:
            s ='The general public (%d) %s : %s' % ((self.votep + self.voten), 'agrees' if self.vote > 0 else 'disagrees', self.ques)
        else:
            s = 'The outcome is a draw! Bummer.'
        
        Thread(target=self.callback, args=(s, )).start()