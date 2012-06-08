'''
Created on Jun 7, 2012
@author: Nisheeth
'''
from QircBot.QircBot import QircBot    

def client(qb):    
    cont_loop = True
    qb.parse_cmd('join #nbaztec')  # Join a channel automatically
    while cont_loop:        
        try:            
            cmd = raw_input('-> ')
            cont_loop = qb.parse_cmd(cmd)
        except:   
            pass         

if __name__ == '__main__':   
    qb = QircBot(client, {
              'host'        : 'irc.freenode.net',
              'port'        : 6667,
              'nick'        : 'QircBot',
              'ident'       : 'QircBot',
              'realname'    : 'QirckyBot'
              })
    if qb.connect():
        qb.register()
        qb.begin_read()    