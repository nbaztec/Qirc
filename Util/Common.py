'''
Created on Oct 15, 2012

@author: Nisheeth
'''

def chunk(l, n):
    '''
        @param l: The list to chunk
        @param n: Number of elements per chunk
        @summary: Splits a list into chunks having n elements each
    '''
    return [l[i:i+n] for i in range(0, len(l), n)]