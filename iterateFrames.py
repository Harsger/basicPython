import sys
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backend_bases import NavigationToolbar2, Event

if int(mpl.__version__[0]) > 2 :
    from matplotlib.backend_tools import ToolBase
    plt.rcParams['toolbar'] = 'toolmanager'

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
                "rangeMax"      :   None ,
                "threshold"     :      5 ,
                "commonMode"    : "none"
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

    print(" ["+str(vmin)+","+str(vmax)+"]")

    if int(mpl.__version__[0]) < 3 :
        column_array = np.arange(-0.5,int(parameters["ncols"]),1)
        row_array    = np.arange(-0.5,int(parameters["nrows"]),1)
    else :
        column_array , row_array = np.meshgrid(
                        np.arange(0,int(parameters["ncols"]),1) ,
                        np.arange(0,int(parameters["nrows"]),1)
                    )

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
    else :
        drawables["cb"].mappable.set_clim( vmin=vmin , vmax=vmax )

    plt.tight_layout()

    if parameters["toShow"] :
        parameters["toShow"] = False
        plt.show()
    else :
        plt.draw()

if int(mpl.__version__[0]) > 2 :

    class new_back(ToolBase) :
        def trigger(self, *args, **kwargs) :
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

    class new_forward(ToolBase) :
        def trigger(self, *args, **kwargs) :
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

    class new_home(ToolBase) :
        def trigger(self, *args, **kwargs) :
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

else :

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

def calculateBasics():
    global parameters , data
    if parameters["mapFile"] != None :
        dataCor = data
        offsetEstimate = 0.
        commonMode = 0.
    else :
        offsetEstimate = np.median( data , axis=0 )
        if parameters["commonMode"] == "COLUMN" :
            commonMode = np.array([
                np.median(
                            data[
                                : ,
                                c
                                : int(parameters["npixels"])
                                : int(parameters["ncols"])
                            ]
                            -
                            offsetEstimate[
                                c
                                : int(parameters["npixels"])
                                : int(parameters["ncols"])
                            ]
                            ,
                            axis=1
                        )
                for c in range( int(parameters["ncols"]) )
            ]).transpose()
            dataCor = np.array([
                np.subtract(
                    data[
                            : ,
                            c
                            : int(parameters["npixels"])
                            : int(parameters["ncols"])
                    ].transpose() ,
                    commonMode[:,c]
                ).transpose()
                for c in range( int(parameters["ncols"]) )
            ]).transpose((1,2,0)).reshape( (
                int(parameters["nframes"]) , int(parameters["npixels"])
            ) )
        else :
            commonMode = np.array([
                np.median(
                            data[
                                : ,
                                r*int(parameters["ncols"])
                                : (r+1)*int(parameters["ncols"])
                            ]
                            -
                            offsetEstimate[
                                r*int(parameters["ncols"])
                                : (r+1)*int(parameters["ncols"])
                            ]
                            ,
                            axis=1
                        )
                for r in range( int(parameters["nrows"]) )
            ]).transpose()
            dataCor = np.array([
                np.subtract(
                    data[
                        : ,
                        r*int(parameters["ncols"])
                        : (r+1)*int(parameters["ncols"])
                    ].transpose() ,
                    commonMode[:,r]
                ).transpose()
                for r in range( int(parameters["nrows"]) )
            ]).transpose((1,0,2)).reshape( (
                int(parameters["nframes"]) , int(parameters["npixels"])
            ) )
    modeVariation = np.std( commonMode )
    print( " common mode variation " + str( modeVariation ) )
    underThreshold = np.abs( dataCor - offsetEstimate ) \
                     < float(parameters["threshold"]) * modeVariation
    accumulation = np.sum( underThreshold , axis=0 )
    print(
            " over threshold ["
            +str( int(parameters["nframes"]) - accumulation.max() )
            +","
            +str( int(parameters["nframes"]) - accumulation.min() )
            +"]"
    )
    if int(np.__version__[2:4].replace(".","")) > 19 :
        parameters["offset"] = \
                        np.mean( dataCor , axis=0 , where=underThreshold )\
                          .reshape( parameters["frameSize"] )
        parameters["noise" ] = \
                        np.std(  dataCor , axis=0 , where=underThreshold )\
                          .reshape( parameters["frameSize"] )
    else :
        baseline = np.where( underThreshold , dataCor , float("nan") )
        parameters["offset"] = np.nanmean( baseline , axis=0 )\
                                 .reshape( parameters["frameSize"] )
        parameters["noise" ] = np.nanstd(  baseline , axis=0 )\
                                .reshape( parameters["frameSize"] )

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
    if len( data ) == 0:
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
###############################################################################
#    print(" reshaping data ... ")
#    data = data.reshape( (
#                            parameters["nframes"] ,
#                            int(parameters["nrows"]) ,
#                            int(parameters["ncols"])
#                        ) )
#    data = data.transpose( ( 0 , 2 , 1 ) )
#    data = data.reshape( ( parameters["nframes"] , parameters["npixels"] ) )
###############################################################################
    if parameters["mapFile"] != None:
        parameters["rowmap"] = np.load( parameters["mapFile"] )["rowmap"   ]
        parameters["colmap"] = np.load( parameters["mapFile"] )["columnmap"]
        if parameters["rowmap"].shape[0] == 1:
            parameters["rowmap"] = parameters["rowmap"][0]
            parameters["colmap"] = parameters["colmap"][0]
        elif parameters["rowmap"].shape[1] == 1:
            parameters["rowmap"] = parameters["rowmap"][:,0]
            parameters["colmap"] = parameters["colmap"][:,0]
        parameters["frameSize"] = tuple( parameters["rowmap"].shape )
    if parameters["offsetFile"] == "none" :
        print(" OFFSET from current file ")
        if parameters["commonMode"] in [ "ROW" , "COLUMN" ] :
            calculateBasics()
        else :
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
        if parameters["commonMode"] in [ "ROW" , "COLUMN" ] :
            swapData = data
            data = offsetData
            parameters["nframes"] = offsetData.shape[0]
            calculateBasics()
            data = swapData
            parameters["nframes"] = data.shape[0]
        else :
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
    parameters["toShow"] = True
    if int(mpl.__version__[0]) > 2 :
        tm = drawables["fig"].canvas.manager.toolmanager
        tm.add_tool( "<" , new_back )
        tm.add_tool( "o" , new_home )
        tm.add_tool( ">" , new_forward )
        drawables["fig"].canvas.manager.toolbar.add_tool(
                                                            tm.get_tool("<") ,
                                                            "toolgroup"
                                                        )
        drawables["fig"].canvas.manager.toolbar.add_tool(
                                                            tm.get_tool("o") ,
                                                            "toolgroup"
                                                        )
        drawables["fig"].canvas.manager.toolbar.add_tool(
                                                            tm.get_tool(">") ,
                                                            "toolgroup"
                                                        )
    draw_current_frame()

if __name__ == "__main__":
    main(sys.argv[1:])

