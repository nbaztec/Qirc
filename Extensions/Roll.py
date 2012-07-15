'''
Created on Jun 10, 2012

@author: Nisheeth
'''

import random

def roll(m=1, n=6):
    '''
        @var m: The lower limit
        @var n: The upper limit
        @summary: Rolls a random number between m and n 
    '''   
    return str(random.randint(m, n))
    