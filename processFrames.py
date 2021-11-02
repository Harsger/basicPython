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
                "batchSize"      :         "none" ,
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
        parameters["rowmap"] = np.load( parameters["mapFile"] )["rowmap"   ]
        parameters["colmap"] = np.load( parameters["mapFile"] )["columnmap"]
        if parameters["rowmap"].shape != parameters["colmap"].shape:
            print(" ERROR : unequal-sized row- and column-maps")
            sys.exit(5)
        if parameters["rowmap"].shape[0] == 1:
            parameters["rowmap"] = parameters["rowmap"][0]
            parameters["colmap"] = parameters["colmap"][0]
        elif parameters["rowmap"].shape[1] == 1:
            parameters["rowmap"] = parameters["rowmap"][:,0]
            parameters["colmap"] = parameters["colmap"][:,0]
    if( 
        np.amax( parameters["rowmap"] )+1 != int(parameters["nrows"])
        or
        np.amax( parameters["colmap"] )+1 != int(parameters["ncols"])
    ):
        print(" ERROR : mapping does not fit specification ")
        sys.exit(6)

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
    print(" CREATE "+str(writename))
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
                            np.arange( float(parameters["ncols"]) ) , 
                            (int(parameters["nrows"]),1) 
                        ).flatten()
        transposeOrder = np.transpose(
                            np.tile( 
                                    np.arange( float(parameters["nrows"]) ) , 
                                    (int(parameters["ncols"]),1) 
                            )
                        ).flatten()
    else:
        lineOrder      = parameters["rowmap"].astype(float).flatten()
        transposeOrder = parameters["colmap"].astype(float).flatten()
    print(" -underflow ")
    sys.stdout.flush()
    outflowData = np.sum( 
                            ( data <= int(parameters["rangeMin"]) ) ,
                            axis  =     0 ,
                            dtype = float
                        ).flatten()
    h_underflowPixels.FillN( 
                                outflowData.size , 
                                transposeOrder , 
                                lineOrder , 
                                outflowData 
                            )
    print(" -overflow  ")
    sys.stdout.flush()
    outflowData = np.sum( 
                            ( data >= int(parameters["rangeMax"]) ) ,
                            axis  =     0 ,
                            dtype = float
                        ).flatten()
    h_overflowPixels.FillN( 
                                outflowData.size , 
                                transposeOrder , 
                                lineOrder , 
                                outflowData 
                            )
    if parameters["batchSize"].isdigit() :
        framesPERbatch = int(parameters["batchSize"])
        nbatches = int(parameters["nframes"]) / framesPERbatch
        if int(parameters["nframes"]) < nbatches * framesPERbatch :
            nbatches += 1
    else:
        framesPERbatch = int(parameters["nframes"])
        nbatches = 1
    dimensions[0] = framesPERbatch
    h_valuePerChannel = [ [] , [] ]
    print(" ITERATE ")
    for d in range(2):
        if d == 1: print(" -ROWS > colDivision ",end=" ")
        else:      print(" -COLS > rowDivision ",end=" ")
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
                                    ( framesPERbatch , 1 , 1 ) 
                                )
            lineOrder = lineOrder.flatten()
        else:
            lineOrder      = parameters[str(toUse)+"map"]
            transposeOrder = parameters[str(other)+"map"]
        weights = np.ones( ( 
                                framesPERbatch , 
                                nbins , 
                                divisionWidth 
                            ) ).flatten()
        for r in range( ndivisions ):
            if ndivisions > 1 :
                if nbatches > 1 : print(" \n --"+str(r),end=": ")
                else :            print(":"  +str(r),end="" )
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
                for b in range(nbatches):
                    batchStart = framesPERbatch * b
                    batchEnd   = framesPERbatch * ( b + 1 )
                    toFill = data[
                                    batchStart: batchEnd ,
                                    rowStart  : rowEnd   ,
                                    colStart  : colEnd
                                ].flatten().astype(float)
                    h_valuePerChannel[d][r].FillN(
                        toFill.size ,
                        lineOrder ,
                        toFill ,
                        weights
                    )
            else:
                mask = np.logical_and( 
                            transposeOrder >= divisionWidth * r , 
                            transposeOrder <  divisionWidth * ( r + 1 )
                        )
                channelNumbers = np.tile( 
                                            lineOrder[ mask ] ,
                                            tuple(dimensions)
                                        ).flatten()
                weights = np.tile( mask[ mask ] , tuple(dimensions) ).flatten()
                for b in range(nbatches):
                    if b > 0 and int(b)%(int(nbatches)/10)==0:
                        print(str(int(float(b)/float(nbatches)*100)),end="% ")
                        sys.stdout.flush()
                    batchStart = framesPERbatch * b
                    batchEnd   = framesPERbatch * ( b + 1 )
                    if batchEnd == int(parameters["nframes"]):
                        batchEnd += 1
                    toFill = data[ batchStart:batchEnd , mask ].flatten()
                    h_valuePerChannel[d][r].FillN(
                        toFill.size ,
                        channelNumbers.astype(float) ,
                        toFill.astype(float) ,
                        weights.flatten().astype(float)
                    )
        print("")
    print(" WRITE ")
    outfile.Write()
    print(" CLOSE ")
    outfile.Close()

if __name__ == "__main__":
    main(sys.argv[1:])

