# -*- coding: utf-8 -*-

import sys, getopt
import os
import time
import math
import csv
import time
from array import array

def readTextFile( fileTOread , seperator = ' ' ):
    
    fileContent = []
    
    inputfile = open( str( fileTOread ) , 'r' )
    
    if inputfile.closed :
        print " WARNING : file \'"+str(fileTOread)+"\' can not be opened "
        return fileContent

    useSeperator = True
    if not seperator :
        useSeperator = False
    
    for line in inputfile:
        
        words = {}
        
        if useSeperator : words = line.split(seperator)
        else: words = line.split()
        
        if len(words) == 0 : continue
        
        fileContent.append(words)
        
    return fileContent

def main(argv):
        
    filename = ''
    expectedCluster = 1
    seperator = ''
    debug = False
    usage = ' python clusterator.py -f <filename> -e <expectedCluster> -s <seperator> -D'

    try:
        
        opts, args = getopt.getopt( argv , "hf:e:s:D" ,["command=","filename=","expectedCluster=","seperator=","DebugMode"] )
        
    except getopt.GetoptError:
        
        print usage
        sys.exit(2)
        
    if len(argv) < 1:
        
        print " arguments required "
        print str(usage)
        sys.exit(2)
        
    for opt, arg in opts:
        
        if opt in ("-h", "--help"):
            print usage
            print " D option enables debug mode "
            print " programm is intended for finding cluster of numerical data in text files "
            sys.exit()
            
        elif opt in ("-f", "--filename"):
            filename = arg
            
        elif opt in ("-e", "--expectedCluster"):
            expectedCluster = arg
            
        elif opt in ("-s", "--seperator"):
            seperator = arg
            
        elif opt in ("-D", "--DebugMode"):
            debug = True
                    
    print " filename        : "+str(filename)
    print " expectedCluster : "+str(expectedCluster)
    if debug : print " debug mode : enabled"
    
    data = readTextFile( filename , seperator )
    
    print " # filled lines in file : "+str( len( data ) )

if __name__ == "__main__":
  main(sys.argv[1:])
