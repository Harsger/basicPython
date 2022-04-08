# -*- coding: utf-8 -*-

import sys
import copy
import math
import time
import datetime
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy import odr

parameters = {
                "parameterFile"    : None                ,
                "dataFile"         : None                ,
                "dateNtimeFormat"  : "%Y-%m-%dT%H:%M:%S" ,
                "timeColumn"       : 0                   ,
                "valueColumn"      : 3                   ,
                "specifierColumns" : [ 2 , 1 , 4 ]       ,
                "lineModulo"       : 100000
            }

timeInput = []
timeIntervals = []
specifier = {
                'x' : [] ,
                'y' : []
            }
axisNames = {
                'x' : ["ABSCISSA","abscissa","X","x"] ,
                'y' : ["ORDINATA","ordinata","Y","y"]
            }
data = {}

def readParameterInput(argv):
    global parameters , specifier , timeInput
    if len(argv) < 1:
        print(" ERROR : no input specified ")
        sys.exit(1)
    parameters["parameterFile"] = argv[0]
    with open(parameters["parameterFile"],'r') as parameterFile:
        line = parameterFile.readline()
        while line:
            words = line.split()
            line = parameterFile.readline()
            if( len(words) < 1 or words[0].startswith("#") ) : continue
            if( len(words) > 2 and words[0] == "TIME" ) :
                timePoints = [ words[1] , words[2] ]
                timeInput.append( timePoints )
                continue
            if len(words) > 1 :
                xORy = None
                for z in [ 'x' , 'y' ] :
                    if words[0] in axisNames[z] :
                        xORy = z
                if xORy != None :
                    specifier[xORy] = [] 
                    for w in range(len(words)-1) :
                        specifier[xORy].append( words[w+1] )
                    continue
            if( len(words) > 1 and words[0] == "specifierColumns" ) :
                parameters["specifierColumns"] = []
                for w in range(len(words)-1) :
                    parameters["specifierColumns"].append( int(words[w+1]) )
            if( len(words) < 2 ): continue
            phrase = ""
            for w in range( len(words)-1 ) :
                phrase += words[w+1]
            parameters[words[0]] = phrase
    if parameters["dataFile"] == None:
        print(" ERROR : no dataFile specified ")
        sys.exit(2)
    if( 
        len(specifier['x']) != len(parameters["specifierColumns"]) 
        or 
        len(specifier['y']) != len(parameters["specifierColumns"]) 
    ) :
        print(" ERROR : abscissa and ordinata has to be specified ")
        print("         and must have same number of arguments as ")
        print("         specifierColumns "
                         +str(len(parameters["specifierColumns"])) )
        sys.exit(3)
    if len(timeInput) < 2 :
        print(" ERROR : at least two timeIntervals requried ")
        sys.exit(4)

def formatTimeInput():
    global parameters , timeInput , timeInvervals
    for startNend in timeInput :
        if len(startNend) != 2 : continue
        for t in range(2) :
            if not startNend[t].isdigit() :
                dateNtimeFormatted = datetime.datetime.strptime( 
                                        startNend[t] , 
                                        parameters["dateNtimeFormat"] 
                                    )
                startNend[t] = datetime.datetime.timestamp( 
                                        dateNtimeFormatted )
        timeIntervals.append( startNend ) 
    if len(timeIntervals) < 2 :
        print(" ERROR : at least two timeIntervals required ")
        sys.exit(5)

def getMagnitudeFormat( magnitude , additionalDigit = 0 ) :
    magFormat = '.'+str(additionalDigit)+'E'
    if 0 <= magnitude < 3 :
        decimals = 0
        if additionalDigit > magnitude :
            decimals = additionalDigit - magnitude
        magFormat = '.'+str(decimals)+'f'
    elif -3 <= magnitude < 0 :
        magFormat = '.'+str(abs(magnitude)+additionalDigit)+'f'
    return magFormat

def getFormatFromError( number , error ) :
    numMag = int( math.floor( math.log10( abs( number ) ) ) )
    errMag = int( math.floor( math.log10( abs( error  ) ) ) )
    numFormat = ''
    errFormat = ''
    if numMag < errMag :
        numFormat = getMagnitudeFormat( numMag )
        errFormat = getMagnitudeFormat( errMag , 1 )
    elif numMag == errMag :
        numFormat = getMagnitudeFormat( numMag , 1 )
        errFormat = getMagnitudeFormat( errMag , 1 )
    else :
        numFormat = getMagnitudeFormat( numMag , numMag-errMag )
        errFormat = getMagnitudeFormat( errMag , 0 )
    return numFormat , errFormat

def getFilename( fullname ) :
    filename = copy.deepcopy( fullname )
    if '/' in filename :
        filename = filename[ filename.rfind('/') : len(filename) ]
    if '.' in filename :
        filename = filename[ 0 : filename.rfind('.') ]
    return filename

def linearFunction( p , x ) :
    return p[0]+p[1]*x

def interceptNslope( x0 , y0 , x1 , y1 ) :
    if x0 == x1 :
        return x0 , x1
    slope = ( y1 - y0 ) / ( x1 - x0 )
    intercept = ( y0 * x1 - y1 * x0 ) / ( x1 - x0 )
    return intercept , slope

def main(argv):

    global parameters , timeIntervals , specifier , data

    readParameterInput(argv)
    formatTimeInput()

    data['x'] = []
    data['y'] = []
    for t in timeIntervals :
        toFill = {
                    "count" : 0  ,
                    "mean"  : 0. ,
                    "stdv"  : 0.
                }
        data['x'].append( toFill )
        data['y'].append( copy.deepcopy( toFill ) )

    numberSpecifier = len( parameters["specifierColumns"] )
    maxColumns = parameters["timeColumn"]
    if maxColumns < parameters["valueColumn"] :
        maxColumns = parameters["valueColumn"]
    for c in parameters["specifierColumns"] :
        if maxColumns < c :
            maxColumns = c
    maxColumns += 1

    timeColumn  = parameters["timeColumn"]
    valueColumn = parameters["valueColumn"] 
    specifierColumns = parameters["specifierColumns"]
    lineCount = 0
    lineModulo = parameters["lineModulo"]

    with open(parameters["dataFile"],'r') as dataFile:
        line = dataFile.readline()
        while line :
            lineCount += 1
            if lineCount % lineModulo == 0 :
                print( " " + str(lineCount) )
            words = line.split()
            line = dataFile.readline()
            if len(words) < maxColumns : continue
            timeString = words[timeColumn]
            if '.' in timeString :
                timeString = timeString[ 0 : timeString.index('.') ]
            unixtime = int( timeString ) 
            interval = -1
            for i , times in enumerate(timeIntervals) :
                if( times[0] <= unixtime and times[1] >= unixtime ) :
                    interval = i
                    break
            if interval < 0 : continue
            xORy = None
            for z in [ 'x' , 'y' ] :
                allWordsFound = True
                for s in range(numberSpecifier) :
                    if words[specifierColumns[s]] != specifier[z][s] :
                        allWordsFound = False
                        break
                if allWordsFound :
                    xORy = z
                    break 
            if xORy == None : continue
            value = float( words[valueColumn] )
            data[xORy][interval]["count"] += 1
            data[xORy][interval]["mean"]  += value
            data[xORy][interval]["stdv"]  += ( value * value )
    
    plotValues = {
                    'x'  : [] ,
                    'y'  : [] ,
                    'ex' : [] ,
                    'ey' : []
    }

    for i , times in enumerate(timeIntervals) :
        print( datetime.datetime
                       .fromtimestamp( times[0] )
                       .strftime( parameters["dateNtimeFormat"] ) 
               , end=" " )
        print( datetime.datetime
                       .fromtimestamp( times[1] )
                       .strftime( parameters["dateNtimeFormat"] ) 
               , end="\t\t" )
        for z in ['x','y'] :
            if data[z][i]["count"] < 1 :
                print( " no data " , end = '' )
                continue
            elif data[z][i]["count"] == 1 :
                data[z][i]["stdv"] = 0.
            else :
                data[z][i]["mean"] /= data[z][i]["count"]
                data[z][i]["stdv"] = math.sqrt( 
                                        (
                                            data[z][i]["stdv"] 
                                            - 
                                            data[z][i]["mean"] 
                                            * data[z][i]["mean"] 
                                            * float( data[z][i]["count"] )
                                        )
                                        / 
                                        ( float( data[z][i]["count"] ) - 1. )
                                    )
            meanFormat , stdvFormat = getFormatFromError(
                data[z][i]["mean"] , data[z][i]["stdv"]
            )
            print(
                    str(data[z][i]["count"])+"# "+
                    format( data[z][i]["mean"] , meanFormat )+"+/-"+
                    format( data[z][i]["stdv"] , stdvFormat ) 
                    , end="\t"
                )
        print("")
        if data['x'][i]["count"] > 0 and data['y'][i]["count"] > 0 :
            plotValues[ 'x'].append( data['x'][i]["mean"] )
            plotValues[ 'y'].append( data['y'][i]["mean"] )
            plotValues['ex'].append( data['x'][i]["stdv"] )
            plotValues['ey'].append( data['y'][i]["stdv"] )
    
    plt.errorbar( 
                    plotValues['x'] , 
                    plotValues['y'] ,
                    yerr = plotValues[ 'ey'] ,
                    xerr = plotValues[ 'ex'] ,
                    color = 'k' ,
                    linestyle = '' ,
                    marker = 'o' ,
                    label = getFilename( parameters['parameterFile'] )
                )

    labels = {
                'x' : "" ,
                'y' : ""
            }
    for z in ['x','y'] :
        labels[z] += specifier[z][0]
        if numberSpecifier == 3 :
            labels[z] += " [ "
            labels[z] += specifier[z][2]
            labels[z] += " ] "

    plt.xlabel(labels['x'])
    plt.ylabel(labels['y'])
    plt.grid(linestyle='--')   

    plotValues[ 'x'] = np.array( plotValues[ 'x'] ) 
    plotValues[ 'y'] = np.array( plotValues[ 'y'] ) 
    plotValues['ex'] = np.array( plotValues['ex'] ) 
    plotValues['ey'] = np.array( plotValues['ey'] ) 
    extrema = [
                [ np.amin( plotValues[ 'x'] ) , np.amax( plotValues[ 'x'] ) ] ,
                [ np.amin( plotValues[ 'y'] ) , np.amax( plotValues[ 'y'] ) ] 
            ]
    estimates = [ 0 , 0 ]
    estimates[0] , estimates[1] = interceptNslope( 
                                    extrema[0][0] , extrema[1][0] ,
                                    extrema[0][1] , extrema[1][1]
                                )

    fitModel = odr.Model( linearFunction )
    fitData  = odr.Data( 
                        plotValues['x'] , 
                        plotValues['y'] ,
                        wd = 1./np.power( plotValues['ex'] , 2 ) ,
                        we = 1./np.power( plotValues['ey'] , 2 )
                    )
    orthogonalDistanceRegression = odr.ODR( 
                                            fitData , 
                                            fitModel , 
                                            beta0=estimates 
                                        )
    fitResult = orthogonalDistanceRegression.run()
#    fitResult.pprint() 
    resultFormat = []
    print( " FIT-RESULT : " )
    for p in range( len( fitResult.beta ) ) :
        resultFormat.append( 
                                getFormatFromError(
                                                    fitResult.beta[p] ,
                                                    fitResult.sd_beta[p]
                                                )
                            )
        print( 
                " P"+str(p)+" : \t "+
                format( fitResult.beta[p]    , resultFormat[p][0] )
                +" +/- "+
                format( fitResult.sd_beta[p] , resultFormat[p][1] )
            ) 
    xValueRange = np.linspace(
                    extrema[0][0] , extrema[0][1] ,
                    len( plotValues['x'] ) * 10
                )
    yFitValues = linearFunction( fitResult.beta , xValueRange )
    plt.plot( 
                xValueRange , yFitValues , 'r' , 
                label = 
                        '( '+
                        format( fitResult.beta[0]    , resultFormat[0][0] )
                        +'+/-'+
                        format( fitResult.sd_beta[0] , resultFormat[0][1] )
                        +' ) + x * ( '+
                        format( fitResult.beta[1]    , resultFormat[1][0] )
                        +'+/-'+
                        format( fitResult.sd_beta[1] , resultFormat[1][1] )
                        +' )'
            )  
    plt.legend( 
        bbox_to_anchor = ( 0. , 1.02 , 1. , .102 ) , 
        mode = "expand" , borderaxespad = 0.
     )

    plt.savefig( str( getFilename( parameters["parameterFile"] ) ) + ".png" )

if __name__ == "__main__":
    main(sys.argv[1:])


