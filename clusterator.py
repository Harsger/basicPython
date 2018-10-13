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



def cartesianDistance( first , second ) :
    
    if len(first) != len(second):
        print " ERROR : points have not the same size"
        return 0

    distance = 0

    for c in range( len(first) ) :
        distance += pow( first[c] - second[c] , 2 )
        
    return math.sqrt( distance )



def kMeansCluster( data , expected=1 , bugger=False ):
    
    stopAt = 100
    
    if expected >= len(data) :
        print " ERROR : not enough data for expectation "
        return data
    
    cluster = data[:expected]
    
    dimensions = len( data[0] )
    
    sameSize = True
    
    for point in data : 
        
        if dimensions != len( point ) :
            sameSize = False
            break
        
    if not sameSize :
        print " ERROR : points in data do not have the same dimension "
        return cluster
    
    maximalDistance = 0
    
    for point in data : 
    
        for other in data : 
            
            distance = cartesianDistance( point , other )
            
            if( maximalDistance < distance ): maximalDistance = distance
    
    pointsINcluster = [[] for c in range(expected)]
    lastPinC = [[] for c in range(expected)]
    
    allocating = True
    fatalError = False
    iteration = 0
    
    while allocating :
        
        if iteration > stopAt :
            print " WARNING : more than "+str(stopAt)+" iterations => aborting "
            break
        
        pointsINcluster = [[] for c in range(expected)]
        
        for point in data : 
            
            minimalDistance = maximalDistance
            nearestCluster = -1
            
            for mean in cluster : 
                
                distance = cartesianDistance( point , mean )
                
                if( minimalDistance > distance ): 
                    minimalDistance = distance
                    nearestCluster = cluster.index(mean)
                    
            if nearestCluster == -1 :
                print " ERROR : no near cluster found "
                fatalError = True
                break
            
            pointsINcluster[nearestCluster].append( data.index(point) )
            
        if fatalError :
            break
        
        newCluster = []
        
        for c in range(expected) :
            
            mean = [0 for d in range(dimensions)]
                
            for d in range(dimensions) :
            
                for p in pointsINcluster[c] :
                    
                    mean[d] += data[p][d]
                
                mean[d] /= len( pointsINcluster[c] )
                
            newCluster.append( mean )
        
        allTheSame = True
        
        for points in pointsINcluster : 
            
            #if bugger :
                #print " points in cluster "+str(pointsINcluster.index(points))
                #strOFpoints = ''
                #for p in points : strOFpoints += ' '+str(p)
                #print str(strOFpoints)
            
            sameClusterFound = False
            
            for other in lastPinC : 
                if len( set(points) & set(other) ) == len(points) : 
                    sameClusterFound = True
                    break
                
            if not sameClusterFound :
                allTheSame = False
                
                
        if allTheSame :
            allocating = False
            break
            
        cluster = newCluster
        lastPinC = pointsINcluster
        
        if bugger : 
            
            print " iteration "+str(iteration)
        
            for mean in cluster :
                
                result = str(cluster.index(mean))+' \t '
                
                for d in range(dimensions) :
                    
                    result += " "+str(mean[d])
                    
                print result+' \t '+str( len( pointsINcluster[ cluster.index(mean) ] ) )
        
        iteration += 1
        
        
    for mean in cluster :
        
        result = str(cluster.index(mean))+' '
        
        for d in range(dimensions) :
            
            result += " "+str(mean[d])
            
        if bugger : print result
        
    return cluster
            
            

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
            expectedCluster = int(float(arg))
            
        elif opt in ("-s", "--seperator"):
            seperator = arg
            
        elif opt in ("-D", "--DebugMode"):
            debug = True
                    
    print " filename        : "+str(filename)
    print " expectedCluster : "+str(expectedCluster)
    if debug : print " debug mode : enabled"
    
    textinput = readTextFile( filename , seperator )
    
    data = [[float(word) for word in line] for line in textinput]
    
    print " # filled lines in file : "+str( len( data ) )
    
    kMeansCluster( data , expectedCluster , debug )

if __name__ == "__main__":
  main(sys.argv[1:])
