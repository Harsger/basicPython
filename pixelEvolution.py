import sys
import numpy as np
import matplotlib.pyplot as plt

parameters = {
                "dataFile" : None ,
                "nrows"    : 64 ,
                "ncols"    : 64 ,
                "col"      : None ,
                "row"      : None
            }

drawables = {
                "fig" : None ,
                "ax"  : None ,
                "pcm" : None ,
                "cb"  : None
            }

data = np.zeros( ( 1 , int(parameters["nrows"]) * int(parameters["ncols"]) ) )

def readData():
    global parameters , data , drawables
    data = np.load( parameters["dataFile"] )
    if len( data ) == 0:
        print(" ERROR : data can not be read ")
        sys.exit(3)
    (parameters["nframes"],parameters["npixels"]) = data.shape
    print( " # frames : " + str(parameters["nframes"]) )
    if( 
        int(parameters["npixels"])
        != 
        int(parameters["nrows"])*int(parameters["ncols"])
    ):
        print( " ERROR : unexpected number of pixels " )
        sys.exit(4)

def main(argv):
    global parameters , data , drawables
    if len(argv) < 3 :
        print(" ERROR : specify data ")
        sys.exit(1)
    parameters["dataFile"] = str(argv[0])
    parameters["col"     ] = int(argv[1])
    parameters["row"     ] = int(argv[2])
    if( 
        parameters["col"] >= parameters["ncols"]
        or
        parameters["row"] >= parameters["nrows"]
    ):
        print(" ERROR : pixel outside of specification ")
        sys.exit(2)
    readData()
    rowStartIndex = parameters["ncols"] * parameters["row"]
    pixelData = data[ : , rowStartIndex + parameters["col"] ]
    rowData   = data[ : , rowStartIndex : (rowStartIndex+parameters["ncols"]) ]
    rowOffset = np.median( rowData , axis=0 )
    commonMode = np.median( rowData - rowOffset , axis=1 )
    print(
            " STDV :"+
            " raw "  +str(np.std(pixelData))+" \t"+
            " cm "   +str(np.std(commonMode))+" \t"+
            " cor "  +str(np.std(pixelData-commonMode))
    )
    if len(argv) > 3 and "write" in str(argv[3]) :
        outname = parameters["dataFile"]
        outname = outname.replace(".npy",".txt")
        nameParts = outname.split("/")
        if len( nameParts ) > 1 :
            outname = nameParts[len(nameParts)-1]
        else :
            outname = nameParts[0]
        print(" writing to : "+str( outname )+" ... ")
        if len(argv) > 3 and "CMC" in str(argv[3]) :
            np.savetxt( outname , pixelData-commonMode , fmt='%i' )
        else :
            np.savetxt( outname , pixelData , fmt='%i' )
        print(" finished ")
    else :
        rawLabel = ""
        if len(argv) > 3 and "CMC" in str(argv[3]) :
            rawLabel = "raw data"
        plt.plot( pixelData , label=rawLabel )
        if len(argv) > 3 and "CMC" in str(argv[3]) :
            plt.plot( pixelData - commonMode , label='common mode corrected' )
            plt.legend()
        plt.show()

if __name__ == "__main__":
    main(sys.argv[1:])
