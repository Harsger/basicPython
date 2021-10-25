import sys
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backend_bases import NavigationToolbar2, Event

parameters = {
                "parameterFile" :   None ,
                "dataFile"      :   None ,
                "mapFile"        :           None ,
                "ncols"         :     64 ,
                "nrows"         :     64 ,
                "nframes"       :      1 ,
                "frame_index"   :      0 ,
                "start_frame"   :      0 ,
                "last_frame"    :      0 ,
                "noise"         :   None ,
                "offset"        :   None ,
                "offsetFile"    : "none" ,
                "rangeMin"      :   None ,
                "rangeMax"      :   None 
            }

drawables = {
                "fig" : None ,
                "ax"  : None ,
                "pcm" : None ,
                "cb"  : None
            }

data = np.zeros( ( 1 , int(parameters["ncols"]) , int(parameters["nrows"] ) ) )

def draw_current_frame():
    global parameters , data , drawables
    
    if int(parameters["nframes"]) != data.shape[0]:
        parameters["nframes"] = data.shape[0]
        
    if( 
        int(parameters["frame_index"]) > int(parameters["nframes"])
        or
        int(parameters["frame_index"]) < -1
    ):
        return
    
    if int(parameters["frame_index"]) == -1:
        singleFrame = parameters["offset"]
        drawables["ax"].set_title("offset")
    elif int(parameters["frame_index"]) == int(parameters["nframes"]):
        singleFrame = parameters["noise"]
        drawables["ax"].set_title("noise")
    else:
        singleFrame = np.reshape( 
                                    data[parameters["frame_index"]] , 
                                    parameters["frameSize"]
                                )
        singleFrame = singleFrame - parameters["offset"]
        drawables["ax"].set_title("frame "+str(parameters["frame_index"]))
    
    if parameters["rangeMin"] != None:
        vmin = int(parameters["rangeMin"])
    else:
        vmin = np.amin( singleFrame )
    if parameters["rangeMax"] != None:
        vmax = int(parameters["rangeMax"])
    else:
        vmax = np.amax( singleFrame )
    norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
    
    column_array = np.arange(-0.5,int(parameters["ncols"]),1)
    row_array    = np.arange(-0.5,int(parameters["nrows"]),1)
    
    if parameters["mapFile"] != None:
        drawFrame = np.zeros( ( 
                                int(parameters["nrows"]) , 
                                int(parameters["ncols"]) 
                            ) )
        drawFrame[
                    parameters["rowmap"].flatten() , 
                    parameters["colmap"].flatten()
                ] = singleFrame.flatten()
        singleFrame = drawFrame
    
    drawables["pcm"] = drawables["ax"].pcolormesh( 
                            column_array , 
                            row_array , 
                            singleFrame , 
                            norm=norm , 
                            shading='nearest' 
                        )
    drawables["ax"].set_xlabel("columns")
    drawables["ax"].set_ylabel("rows")
    if drawables["cb"] == None:
        drawables["cb"] = drawables["fig"].colorbar(
                                                    drawables["pcm"] , 
                                                    ax=drawables["ax"] ,
                                                    norm=norm
                                                )
        drawables["cb"].ax.set_ylabel("ADU")
    else:
        drawables["cb"].on_mappable_changed( drawables["pcm"] )
    plt.tight_layout()
    plt.show()

back = NavigationToolbar2.back
def new_back(self, *args, **kwargs):
    global parameters , data , drawables
    if( 
        int(parameters["frame_index"]) > 0
        and
        int(parameters["frame_index"]) != int(parameters["nframes"])
    ):
        parameters["frame_index"]=int(parameters["frame_index"])-1
    else:
        parameters["frame_index"]=int(parameters["start_frame"])
    draw_current_frame()
    back(self, *args, **kwargs)
NavigationToolbar2.back = new_back

forward = NavigationToolbar2.forward
def new_forward(self, *args, **kwargs):
    global parameters , data , drawables
    if( 
        int(parameters["frame_index"]) < int(parameters["nframes"])
        and
        int(parameters["frame_index"]) != -1
    ):
        parameters["frame_index"]=int(parameters["frame_index"])+1
    else:
        parameters["frame_index"]=int(parameters["start_frame"])
    draw_current_frame()
    forward(self, *args, **kwargs)
NavigationToolbar2.forward = new_forward

home = NavigationToolbar2.home
def new_home(self, *args, **kwargs):
    global parameters , data , drawables
    if( 
        int(parameters["frame_index"]) != -1
        and
        int(parameters["frame_index"]) != int(parameters["nframes"])
    ):
        parameters["last_frame"] = int(parameters["frame_index"])
        parameters["frame_index"] = -1
    elif parameters["frame_index"] != int(parameters["nframes"]):
        parameters["frame_index"] = int(parameters["nframes"])
    else:
        parameters["frame_index"]=int(parameters["last_frame"])
    draw_current_frame()
    home(self, *args, **kwargs)
NavigationToolbar2.home = new_home

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
    parameters["frameSize"] = ( 
                                int(parameters["ncols"]) , 
                                int(parameters["nrows"]) 
                            ) 
    if parameters["mapFile"] != None:
        parameters["rowmap"] = np.load( parameters["mapFile"] )["rowmap"   ][0]
        parameters["colmap"] = np.load( parameters["mapFile"] )["columnmap"][0]
        parameters["frameSize"] = tuple( parameters["rowmap"].shape )
    if parameters["offsetFile"] == "none" :
        print(" OFFSET from current file ")
        parameters["offset"] = np.reshape( 
                                            np.average( data , axis=0 ), 
                                            parameters["frameSize"]
                                        )
        parameters["noise" ] = np.reshape( 
                                            np.std( data , axis=0 ) , 
                                            parameters["frameSize"] 
                                        )
    elif parameters["offsetFile"].endswith(".npy") :
        print(" OFFSET from provided file ")
        offsetData = np.load( parameters["offsetFile"] )
        parameters["offset"] = np.reshape( 
                                            np.average( offsetData , axis=0 ), 
                                            parameters["frameSize"]
                                        )
        parameters["noise" ] = np.reshape( 
                                            np.std( offsetData , axis=0 ), 
                                            parameters["frameSize"]
                                        )
    else:
        print(" no OFFSET subtraction ")
        parameters["offset"] = np.zeros( parameters["frameSize"] )
        parameters["noise" ] = np.zeros( parameters["frameSize"] )

def main(argv):
    global parameters , data , drawables
    readParameterInput(argv)
    parameters["frame_index"] = int(parameters["start_frame"])
    drawables["fig"] , drawables["ax"] = plt.subplots()
    draw_current_frame()

if __name__ == "__main__":
    main(sys.argv[1:])