# -*- coding: utf-8 -*-

import sys
import copy
import math
import time
from datetime import datetime
import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
#from scipy.optimize import curve_fit
#from scipy import odr

secondsPER = {
    ""       :        1 , #
    "s"      :        1 , #
    "second" :        1 , #
    "m"      :       60 , #
    "minute" :       60 , #
    "h"      :     3600 , #            60 * 60
    "hour"   :     3600 , #            60 * 60
    "d"      :    86400 , #       24 * 60 * 60
    "day"    :    86400 , #       24 * 60 * 60
    "w"      :   604800 , #   7 * 24 * 60 * 60
    "week"   :   604800 , #   7 * 24 * 60 * 60
    "M"      :  2678400 , #   31* 24 * 60 * 60
    "month"  :  2678400 , #   31* 24 * 60 * 60
    "y"      : 31536000 , # 365 * 24 * 60 * 60
    "year"   : 31536000 , # 365 * 24 * 60 * 60
}

class TimeAxisItem( pg.AxisItem ) :
    def __init__( self , *args , **kwargs ) :
        super( TimeAxisItem , self ).__init__( *args , **kwargs )
    def tickStrings( self , values , scale , spacing ) :
        global secondsPER
        ticks = []
        if not values :
            return []
        milliseconds = False
        if   spacing >= secondsPER[  "year"] * 3 :
            timeFormat = "%Y"
        #elif spacing >= secondsPER[ "month"] * 3 :
            #timeFormat = "%d.%m.%Y"    
        elif spacing >= secondsPER[   "day"] * 3 :
            timeFormat = "%d.%m."
        #elif spacing >= secondsPER[  "hour"] * 3 :
            #timeFormat = "%H:%M"
        elif spacing >= secondsPER["minute"] * 3 :
            timeFormat = "%H:%M"
        elif spacing >= 3 :
            timeFormat = "%H:%M:%S"
        else:
            timeFormat = "%H:%M:%S.%f"
            milliseconds = True
        for v in values:
            try:
                if milliseconds:
                    ticks.append(
                        datetime.fromtimestamp(v)
                                .strftime(timeFormat).rstrip("0")+"\""
                    )
                else:
                    ticks.append( 
                        datetime.fromtimestamp(v).strftime(timeFormat) 
                    )
            except ValueError:
                ticks.append( "" )
        return ticks
    def attachToPlotItem( self , plotItem ) :
        self.setParentItem( plotItem )
        viewBox = plotItem.getViewBox()
        self.linkToView( viewBox )
        self._oldAxis = plotItem.axes[ self.orientation ][ 'item' ]
        self._oldAxis.hide()
        plotItem.axes[ self.orientation ][ 'item' ] = self
        pos = plotItem.axes[ self.orientation ][ 'pos' ]
        old_item = plotItem.layout.itemAt(*pos)
        plotItem.layout.removeItem(old_item)
        plotItem.layout.addItem( self , *pos )
        self.setZValue(-1000)

parameters = {
                "dataFile"         : None                ,
                "parameterFile"    : None                ,
                "dateNtimeFormat"  : "%Y-%m-%dT%H:%M:%S" ,
                "timeZoneHour"     : 1                   ,
                "timeColumn"       : 0                   ,
                "valueColumn"      : 3                   ,
                "specifierColumns" : [ 2 , 1 , 4 ]       ,
                "markerSize"       : 1.                  ,
                "plotWidth"        : 800                 ,
                "plotHeight"       : 200                 ,
                "plotBackground"   : "white"             ,
                "plotGrid"         : ""
            }

specifiers = []
timeInput = []
quantityUnits = {}
plots = {}
data = []
timeRange = []

def readParameterInput( argv ) :
    global parameters , specifiers , timeInput , plots
    argc = len( argv )
    if argc < 1 :
        print(" ERROR : at least two arguments required for plotting")
        print("         -> data-file-name and parameter-file-name ")
        sys.exit(1)
    parameters["dataFile"] = argv[0]
    if argc < 2 :
        print(" INFO : second argument (parameter-file) required for plotting")
        print("        -> list with specifier and quantities to plot ")
        return
    parameters["parameterFile"] = argv[1]
    if argc > 2 :
        timeInput.append( argv[2] )
    if argc > 3 :
        timeInput.append( argv[3] )
    with open(parameters["parameterFile"],'r') as parameterFile:
        line = parameterFile.readline()
        while line:
            words = line.split()
            line = parameterFile.readline()
            wordCount = len(words)
            if( wordCount < 1 or words[0].startswith("#") ) : continue
            if( words[0] == "PARAMETER" and wordCount > 2 ) :
                parameters[ words[1] ] = words[2]
                continue
            if( words[0] == "PLOT" and wordCount > 1 ) :
                singlePlot = []
                for w in range( 2 , wordCount ) :
                    if( words[w] != "%" ) :
                        singlePlot.append( words[w] )
                    else :
                        singlePlot.append( "" )
                plots[ words[1] ] = singlePlot
                continue
            if( wordCount > 1 ) :
                specs = [ words[0] , words[1] ]
                if( wordCount > 2 and words[2] != "%" ) :
                    specs.append( words[2] )
                else :
                    specs.append( "" )
                for w in range( 3 , wordCount ) :
                    if words[w] == "%" :
                        specs.append( "" )
                    else :
                        specs.append( words[w] )
                specifiers.append( specs )
    if( 
        parameters["dataFile"] == None
        or parameters["parameterFile"] == None
        or len( specifiers ) < 1
    ) :
        print(" ERROR : input not well specified ")
        sys.exit(2)

def readData() :
    global parameters , specifiers , data , timeInput , timeRange
    rawData = np.loadtxt( parameters["dataFile"] , dtype='U' )
    if rawData.shape[0] < 1 :
        print(" ERROR : data empty ")
        sys.exit(3)
    print(" data : "+str( rawData.shape[0] ) )
    swapValues = False
    startColumn = int( parameters["timeColumn"] )
    endColumn   = int( parameters["valueColumn"] )
    timeRange.append( np.min( rawData[:,startColumn].astype(float) ) )
    timeRange.append( np.max( rawData[:,startColumn].astype(float) ) )
    print(
            " time : "
            +str( datetime.fromtimestamp( timeRange[0] )
                          .strftime( parameters["dateNtimeFormat"] )
                )
            +" to "
            +str( datetime.fromtimestamp( timeRange[1] )
                          .strftime( parameters["dateNtimeFormat"] )
                )
        )
    if len( timeInput ) == 2 :
        for t in range(2) :
            timeRange[t] = ( 
                                datetime.strptime( 
                                    timeInput[t] ,
                                    parameters["dateNtimeFormat"]
                                )
                                - 
                                datetime(
                                            1970 , 1 , 1 ,
                                            int( parameters[ "timeZoneHour" ] )
                                        )
                            ).total_seconds()
    if startColumn > endColumn :
        swapValues = True
        startColumn , endColumn = endColumn , startColumn
    columnStride = endColumn - startColumn
    endColumn = endColumn+1
    if parameters["parameterFile"] == None :
        uniqueSpecifier = np.unique(
                                rawData[
                                    : , int(parameters["specifierColumns"][0])
                                ]
                            )
        uniqueQuantities = np.unique(
                                rawData[
                                    : , int(parameters["specifierColumns"][1])
                                ]
                            )
        for s in uniqueSpecifier :
            for q in uniqueQuantities :
                specifiers.append( [ s , q , "" ] )
    for spec in specifiers :
        equalTOspecifier = np.array(
                                rawData[
                                    : , int(parameters["specifierColumns"][0])
                                ]
                                ==
                                spec[0]
                            )
        equalTOquantity  = np.array(
                                rawData[
                                    : , int(parameters["specifierColumns"][1])
                                ] 
                                == 
                                spec[1]
                            )
        timeNvalue       = rawData[
                                np.logical_and(
                                                equalTOspecifier ,
                                                equalTOquantity
                                    ) ,
                                startColumn:endColumn:columnStride
                            ].astype(float)
        if parameters["parameterFile"] == None and timeNvalue.size == 0 :
            continue
        if swapValues :
            timeNvalue[:,[1,0]] = timeNvalue[:,[0,1]]
        print(
                " "+str(spec[0])+
                " "+str(spec[1])+
                " \t "+str( timeNvalue.shape[0] )
            )
        data.append( np.swapaxes( timeNvalue , 0 , 1 ) )
        units = rawData[ 
                            equalTOquantity , 
                            int( parameters["specifierColumns"][2] )
                        ]
        if units.shape[0] > 0 :
            quantityUnits[ spec[1] ] = units[0]
        else :
            quantityUnits[ spec[1] ] = ""
    if parameters["parameterFile"] == None :
        sys.exit(4)

def main(argv):
    global parameters , specifiers , timeInput , plots , data , timeRange
    global secondsPER
    readParameterInput( argv )
    readData()
    app = QtGui.QApplication([])
    defaultColor = 'w'
    if parameters[ "plotBackground" ] == "white" :
        defaultColor = 'k'
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
    win = pg.GraphicsLayoutWidget()
    drawnINplot = []
    for spec in specifiers :
        drawnINplot.append( -1 )
    plotCount = 0
    plotMap = {}
    plotNumber = {}
    for p in plots :
        toFill = False
        quantity = ""
        for spec in specifiers :
            if spec[2] == p :
                quantity = spec[1]
                toFill = True
                break
        if not toFill : continue
        plotNumber[p] = plotCount
        plotMap[p] = win.addPlot( row = plotCount , col = 0 )
        plotMap[p].hideAxis('bottom')
        timeXaxis = TimeAxisItem( orientation = 'bottom' )
        timeXaxis.attachToPlotItem( plotMap[p] )
        plotMap[p].getAxis('bottom').enableAutoSIPrefix( False )
        plotMap[p].addLegend()
        unit = quantityUnits[ quantity ]
        if len( plots[p] ) > 1 :
            unit = plots[p][1]
        plotMap[p].setLabel( 'left' , str(plots[p][0]) , units=str(unit) )
        logYaxis = False
        if len( plots[p] ) > 4 and plots[p][4] == "log" :
            logYaxis = True
            plotMap[p].getAxis('left').enableAutoSIPrefix( False )
            plotMap[p].getAxis('left').setLogMode( True )
            if plots[p][2] != "" and plots[p][3] != "" :
                plotMap[p].setYRange(
                                        np.log10( float( plots[p][2] ) ) ,
                                        np.log10( float( plots[p][3] ) ) ,
                                        padding = 0
                                    )
        elif len( plots[p] ) > 3 and plots[p][2] != "" and plots[p][3] != "" :
            plotMap[p].setYRange(
                                    float( plots[p][2] ) ,
                                    float( plots[p][3] ) ,
                                    padding = 0
                                )
        plotCount += 1
        for c , spec in enumerate( specifiers ) :
            if spec[2] == p :
                drawnINplot[c] = plotNumber[p]
                symbolPen = defaultColor
                symbol    = 'o'
                if len( spec ) > 3 and spec[3] != "" :
                    symbolPen = spec[3]
                    if str( spec[3] ).isdigit() :
                        symbolPen = int( spec[3] )
                if len( spec ) > 4 and spec[4] != "" :
                    symbol    = spec[4]
                if logYaxis :
                    data[c][1] = np.log10( data[c][1] )
                plotMap[p].plot( 
                                data[c][0] , data[c][1] ,
                                name        = str( spec[0] ) ,
                                pen         = None ,
                                symbolBrush = symbolPen ,
                                symbolPen   = None ,
                                symbol      = symbol ,
                                symbolSize  = float( parameters["markerSize"] )
                            )
    for c , spec in enumerate( specifiers ) :
        if drawnINplot[c] > -1 : continue
        if spec[1] not in plotNumber :
            plotNumber[ spec[1] ] = plotCount
            plotMap[ spec[1] ] = win.addPlot( row = plotCount , col = 0 )
            plotMap[ spec[1] ].hideAxis('bottom')
            timeXaxis = TimeAxisItem( orientation = 'bottom' )
            timeXaxis.attachToPlotItem( plotMap[ spec[1] ] )
            plotMap[ spec[1] ].getAxis('bottom').enableAutoSIPrefix( False )
            plotMap[ spec[1] ].addLegend()
            plotCount += 1
        drawnINplot[c] = plotNumber[ spec[1] ]
        symbolPen = defaultColor
        symbol    = 'o'
        if len( spec ) > 3 and spec[3] != "" :
            symbolPen = spec[3]
        if len( spec ) > 4 and spec[4] != "" :
            symbol    = spec[4]
        plotMap[ spec[1] ].plot( 
                                data[c][0] , data[c][1] ,
                                name        = str( spec[0] ) ,
                                pen         = None ,
                                symbolBrush = symbolPen ,
                                symbolPen   = None ,
                                symbol      = symbol ,
                                symbolSize  = float( parameters["markerSize"] )
                            )
        plotMap[ spec[1] ].setLabel( 
                                        'left' , str( spec[1] ) ,
                                        str( quantityUnits[ spec[1] ] ) 
                                    )
    firstPlot = "fillFirstPlot"
    for p in plotMap :
        plotMap[p].setXRange( timeRange[0] , timeRange[1] )
        grid = [ False , False ]
        if "X" in parameters["plotGrid"] :
            grid[0] = True
        if "Y" in parameters["plotGrid"] :
            grid[1] = True
        plotMap[p].showGrid( x = grid[0] , y = grid[1] )
        if firstPlot == "fillFirstPlot" :
            firstPlot = p
        else :
            plotMap[p].setXLink( plotMap[firstPlot] )
        if plotNumber[p] == plotCount-1 :
            timeFormat = "%d.%m.%Y"
            if timeRange[1] - timeRange[0] > secondsPER["day"] * 3. :
                timeFormat = "%Y"
            centerTime = timeRange[0] + 0.5 * ( timeRange[1] - timeRange[0] )
            axisTitle = str( 
                                datetime.fromtimestamp( centerTime )
                                        .strftime(      timeFormat )
                            )
            plotMap[p].setLabel( 'bottom' , axisTitle , units="" )
    win.resize(
                int( parameters[ "plotWidth"  ] ) ,
                int( parameters[ "plotHeight" ] ) * plotCount
            )
    win.show()
    if ( sys.flags.interactive != 1 ) or not hasattr( QtCore, 'PYQT_VERSION' ) :
        QtGui.QApplication.instance().exec_()

if __name__ == "__main__":
    main(sys.argv[1:])
