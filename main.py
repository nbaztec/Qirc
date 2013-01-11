'''
Created on Jun 7, 2012
@author: Nisheeth
'''
from QircBot.QircBot import QircBot
from Util.Log import Log
    
def client(qb):    
    #qb.join('#nbaztec', "yada")                            # Join a channel (with passphrase) automatically
    #qb.join('#nbaztec')                                    # Join a channel automatically
    #qb.notice('nbaztec', "Qirc is now online.")            # Send a notice to a user    
    #print 'Up'												# Print something to terminal
    #time.sleep(10)											# Wait 10 seconds
    #qb.disconnect('')										# Disconnect Bot    
    pass           

if __name__ == '__main__':    
    qb = QircBot(callback=client)
    qb.start()