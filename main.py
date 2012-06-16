'''
Created on Jun 7, 2012
@author: Nisheeth
'''
from QircBot.QircBot import QircBot    
from Util.Log import Log

def client(qb):
    qb.join('#nbaztec')                            # Join a channel automatically
    qb.notice('nbaztec', "Qirc is now online.")
    #print 'Up'
    #time.sleep(10)
    #qb.disconnect('')
    pass           

if __name__ == '__main__':
    #Log.purge()
    #Log.debug = True   
    qb = QircBot(client, {
              'host'        : 'irc.freenode.net',
              'port'        : 6667,
              'nick'        : 'Qirc',
              'ident'       : 'QircBot',
              'realname'    : 'QirckyBot',
              'password'    : 'XXXX',
              })
    
    qb.start()
