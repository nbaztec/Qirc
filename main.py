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
    pass           

if __name__ == '__main__':    
    qb = QircBot(client, {
              'host'        : 'irc.freenode.net',
              'port'        : 6667,
              'nick'        : 'Qirc',
              'ident'       : 'QircBot',
              'realname'    : 'QirckyBot',
              'password'    : 'MacDonald',
              })
    
    qb.start()
