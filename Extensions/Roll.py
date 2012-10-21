'''
Created on Jun 10, 2012

@author: Nisheeth
'''

import random

def roll(m=1, n=6):
    '''
        @param m: The lower limit
        @param n: The upper limit
        @summary: Rolls a random number between m and n 
    '''   
    return str(random.randint(m, n))
    