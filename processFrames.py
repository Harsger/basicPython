from __future__ import print_function
import sys
import numpy as np
import ROOT
from ROOT import TFile , TH2I

parameters = {
                "parameterFile"  :           None ,
                "dataFile"       :           None ,
                "mapFile"        :           None ,
                "outname"        : "results.root" ,
                "nrows"          :             64 ,
                "ncols"          :             64 ,
                "nframes"        :              1 ,
                "rowDivisions"   :              1 ,
                "colDivisions"   :              1 ,
                "noise"          :           None ,
                "offset"         :           None ,
                "offsetFile"     :         "none" ,
                "rangeMin"       :              0 ,
                #"rangeMax"       :          16384 ,
                "rangeMax"       :          16380 ,
                "rangeDivisions" :           1638  
            }

data = np.zeros( (1,int(parameters["nrows"])*int(parameters["ncols"])) )

def readParameterInput(argv):
    global parameters , data
    if len(argv) < 1:
        print(" ERROR : no input specified ")
        sys.exit(1)
    parameters["parameterFile"] = argv[0]
    with open(parameters["parameterFile"],'r') as parameterFile:
        line = parameterFile.readline()
        while line:
            words = line.split()
            line = parameterFile.readline()
            if( len(words)<2 or words[0].startswith("#") ):
                continue
            parameters[words[0]] = words[1]
    if parameters["dataFile"] == None:
        print(" ERROR : no data specified ")
        sys.exit(2)
    print(" LOAD "+str(parameters["dataFile"]))
    data = np.load( parameters["dataFile"] )
    if data == None:
        print(" ERROR : data can not be read ")
        sys.exit(3)
    (parameters["nframes"],parameters["npixels"]) = data.shape
    print( " # frames : " + str(parameters["nframes"]) )
    if( 
        int(parameters["npixels"])/int(parameters["ncols"]) 
        != 
        int(parameters["nrows"]) 
    ):
        print( " ERROR : unexpected number of pixels " )
        sys.exit(4)
    frameSize = ( int(parameters["ncols"]) , int(parameters["nrows"]) ) 
    if parameters["offsetFile"] == "none" :
        print(" OFFSET current file ")
        parameters["offset"] = np.reshape( 
                                            np.average( data , axis=0 ), 
                                            frameSize
                                        )
        parameters["noise" ] = np.reshape( 
                                            np.std( data , axis=0 ) , 
                                            frameSize 
                                        )
    elif parameters["offsetFile"].endswith(".npy") :
        print(" OFFSET provided file ")
        offsetData = np.load( parameters["offsetFile"] )
        parameters["offset"] = np.reshape( 
                                            np.average( offsetData , axis=0 ), 
                                            frameSize
                                        )
        parameters["noise" ] = np.reshape( 
                                            np.std( offsetData , axis=0 ), 
                                            frameSize
                                        )
    else:
        print(" OFFSET not subtracted ")
        parameters["offset"] = np.zeros( frameSize )
        parameters["noise" ] = np.zeros( frameSize )
    if parameters["mapFile"] != None:
        parameters["rowmap"] = np.load( parameters["mapFile"] )["rowmap"   ][0]
        parameters["colmap"] = np.load( parameters["mapFile"] )["columnmap"][0]

def main(argv):
    global parameters , data
    readParameterInput(argv)
    if parameters["mapFile"] == None:
        parameters["dimensions"] = [
                                        int(parameters["nframes"]) , 
                                        int(parameters["nrows"]  ) , 
                                        int(parameters["ncols"]  ) 
                                    ]
    else:
        parameters["dimensions"] = [ parameters["nframes"] ]
        for d in parameters["rowmap"].shape :
            parameters["dimensions"].append(d)
    if len(parameters["dimensions"]) > 3:
        preDivisions = int(parameters["dimensions"][1])
        if( 
            (
                int(parameters["colDivisions"]) < preDivisions
                and
                preDivisions % int(parameters["colDivisions"]) != 0
            )
            or
            (
                int(parameters["colDivisions"]) > preDivisions
                and
                int(parameters["colDivisions"]) % preDivisions != 0
            )
        ):
            print(
                    " ERROR : data-divisions ("+
                    str(preDivisions)+
                    ") do not match specified divisions ("+
                    str(parameters["colDivisions"])+
                    ") "
                )
            sys.exit(5)
        channelsPerDivision = int(parameters["dimensions"][3])
        totalColumns = preDivisions * channelsPerDivision
        if totalColumns != int(parameters["ncols"]) :
            print(
                    " ERROR : data ("+
                    str(totalColumns)+
                    " do not match specified columns ("+
                    str(parameters["ncols"])+
                    ") "
                )
            sys.exit(6)
        totalRows = parameters["dimensions"][2]
        if totalRows != int(parameters["nrows"]) :
            print(
                    " ERROR : data ("+
                    str(parameters["dimensions"][2])+
                    " do not match specified rows ("+
                    str(parameters["nrows"])+
                    ") "
                )
            sys.exit(7)
    else:
        preDivisions = int(parameters["colDivisions"])
        channelsPerDivision = int(parameters["ncols"])/preDivisions
        totalColumns = int(parameters["ncols"])
    print(" RESHAPE ",end="")
    sys.stdout.flush()
    data = np.reshape( data , tuple( parameters["dimensions"] ) )
    print(" > data.shape : "+str(data.shape))
    dimensions = list(parameters["dimensions"])
    for i in range(len(dimensions)): dimensions[i] = 1
    dimensions[0] = parameters["nframes"]
    if parameters["outname"].endswith(".root"):
        writename = parameters["outname"]
    else:
        writename = parameters["parameterFile"] 
        if "." in outname :
            writename = outname[ 0 : outname.rindex(".") ] 
        writename += ".root"
    print(" RECREATE "+str(writename))
    outfile = TFile( writename , "RECREATE" )
    print(" SEARCH ")
    h_underflowPixels = ROOT.TH2D(
                                "underflowPixels" , "underflowPixels" ,
                                int(parameters["ncols"]) , 
                                -0.5 , float(parameters["ncols"])-0.5 ,
                                int(parameters["nrows"]) , 
                                -0.5 , float(parameters["nrows"])-0.5 
                            )
    h_underflowPixels.SetXTitle("column")
    h_underflowPixels.SetYTitle("row")
    h_underflowPixels.SetZTitle("ADU")
    h_overflowPixels = ROOT.TH2D(
                                "overflowPixels" , "overflowPixels" ,
                                int(parameters["ncols"]) , 
                                -0.5 , float(parameters["ncols"])-0.5 ,
                                int(parameters["nrows"]) , 
                                -0.5 , float(parameters["nrows"])-0.5 
                            )
    h_overflowPixels.SetXTitle("column")
    h_overflowPixels.SetYTitle("row")
    h_overflowPixels.SetZTitle("ADU")
    if( parameters["mapFile"] == None ):
        lineOrder = np.tile( 
                        np.tile( 
                            np.arange( float(parameters["ncols"]) ) , 
                            (int(parameters["nrows"]),1) 
                        ) , 
                        (int(parameters["nframes"]),1,1) 
                    ).astype(float)
        transposeOrder = np.tile( 
                            np.transpose(
                                np.tile( 
                                    np.arange( float(parameters["nrows"]) ) , 
                                    (int(parameters["ncols"]),1) 
                                )
                            ) , 
                            (int(parameters["nframes"]),1,1) 
                        ).astype(float)
    else:
        lineOrder      = parameters["rowmap"]
        transposeOrder = parameters["colmap"]
        lineOrder      = np.tile( 
                                    lineOrder , 
                                    tuple(dimensions) 
                                ).astype(float)
        transposeOrder = np.tile( 
                                    transposeOrder , 
                                    tuple(dimensions) 
                                ).astype(float)
    print(" -underflow ",end="")
    sys.stdout.flush()
    outflowData = ( data <= int(parameters["rangeMin"]) ).astype(float)
    print(" > FILL ")
    h_underflowPixels.FillN( 
                                outflowData.size , 
                                transposeOrder.flatten() , 
                                lineOrder.flatten() , 
                                outflowData.flatten() 
                            )
    print(" -overflow ",end="")
    sys.stdout.flush()
    outflowData = ( data >= int(parameters["rangeMax"]) ).astype(float)
    print(" > FILL ")
    h_overflowPixels.FillN( 
                                outflowData.size , 
                                transposeOrder.flatten() , 
                                lineOrder.flatten() , 
                                outflowData.flatten() 
                            )
    h_valuePerChannel = [ [] , [] ]
    print(" ITERATE ")
    for d in range(2):
        if d == 1: print(" -ROWS > colDivision ",end="\t")
        else:      print(" -COLS > rowDivision ",end="\t")
        sys.stdout.flush()
        toUse , other = "col" , "row"
        if d == 1: toUse , other = other , toUse
        nbins = int(parameters["n"+str(toUse)+"s"])
        ndivisions = int(parameters[str(other)+"Divisions"])
        divisionWidth = int(parameters["n"+str(other)+"s"]) / ndivisions
        if parameters["mapFile"] == None:
            lineOrder = np.tile( 
                                    np.arange( float(nbins) ) , 
                                    ( divisionWidth , 1 ) 
                                )
            if d == 1:
                lineOrder = np.transpose( lineOrder )
            lineOrder = np.tile(
                                    lineOrder ,
                                    ( int(parameters["nframes"]) , 1 , 1 ) 
                                )
            lineOrder = lineOrder.flatten()
        else:
            if d == 1: lineOrder = parameters["rowmap"]
            else:      lineOrder = parameters["colmap"]
            lineOrder = np.tile( lineOrder , tuple(dimensions) ).astype(float)
        weights = np.ones( ( 
                                int(parameters["nframes"]) , 
                                nbins , 
                                divisionWidth 
                            ) )
        weights = weights.flatten()
        for r in range( ndivisions ):
            #print(" -- "+str(r))
            print(":"+str(r),end="")
            sys.stdout.flush()
            title = ""
            if d == 1: title += "rowValues_colD"
            else:      title += "colValues_rowD"
            title += str(r)
            h_valuePerChannel[d].append(
                ROOT.TH2I(
                        title , title ,
                        int(nbins) , -0.5 , float(nbins)-0.5 ,
                        int(parameters["rangeDivisions"]) ,
                        float(parameters["rangeMin"]) ,
                        float(parameters["rangeMax"])
                )
            )
            h_valuePerChannel[d][r].SetXTitle("column")
            if d == 1 : h_valuePerChannel[d][r].SetXTitle("row")
            h_valuePerChannel[d][r].SetYTitle("ADU")
            if parameters["mapFile"] == None:
                colStart , colEnd = 0 , nbins
                rowStart , rowEnd = 0 , nbins
                if d == 1:
                    colStart = divisionWidth * r
                    colEnd   = divisionWidth * ( r + 1 )
                else:
                    rowStart = divisionWidth * r
                    rowEnd   = divisionWidth * ( r + 1 )
                h_valuePerChannel[d][r].FillN(
                    weights.size ,
                    lineOrder ,
                    data[:,rowStart:rowEnd,colStart:colEnd]
                                                        .flatten()
                                                        .astype(float) ,
                    weights
                )
            else:
                colStart , colEnd = 0 , preDivisions
                rowStart , rowEnd = 0 , totalRows
                chaStart , chaEnd = 0 , channelsPerDivision
                if d == 1:
                    lowEdge  = r * divisionWidth
                    colStart = lowEdge / channelsPerDivision
                    chaStart = lowEdge % channelsPerDivision
                    uppEdge  = ( r + 1 ) * divisionWidth
                    colEnd   = uppEdge / channelsPerDivision
                    chaEnd   = uppEdge % channelsPerDivision
                    if colEnd == colStart : colEnd += 1
                    if chaEnd == 0        : chaEnd = channelsPerDivision
                else:
                    rowStart = divisionWidth * r
                    rowEnd   = divisionWidth * ( r + 1 )
                h_valuePerChannel[d][r].FillN(
                    weights.size ,
                    lineOrder[
                                : , 
                                colStart:colEnd , 
                                rowStart:rowEnd , 
                                chaStart:chaEnd
                            ]
                            .flatten() ,
                    data[
                            : ,
                            colStart:colEnd , 
                            rowStart:rowEnd , 
                            chaStart:chaEnd
                        ]
                        .flatten().astype(float) ,
                    weights
                )
        print("")
    print(" WRITE ")
    outfile.Write()
    print(" CLOSE ")
    outfile.Close()

if __name__ == "__main__":
    main(sys.argv[1:])