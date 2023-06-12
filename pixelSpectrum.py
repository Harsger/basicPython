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
    pixelData = pixelData - commonMode
    overThreshold = np.abs( 
                            pixelData - rowOffset[ parameters["row"] ] 
                    ) > 5*commonMode
    baseline = np.ma.MaskedArray( pixelData , mask=overThreshold )
    pixelOffset = np.ma.median( baseline )
    pixelNoise  = np.ma.std( baseline )
    pixelData_cor = pixelData - pixelOffset
    signals = np.ma.MaskedArray( 
                                pixelData_cor ,
                                mask = np.abs(pixelData_cor) < 5*pixelNoise
                            )
#    plt.hist( signals , 1E3 , ( 0. , 1E4 ) )
    counts , bins = np.histogram( signals.compressed() , 1000 , ( 0. , 1E4 ) )
    plt.hist( bins[:-1] , bins , weights=counts )
    plt.show()

if __name__ == "__main__":
    main(sys.argv[1:])
