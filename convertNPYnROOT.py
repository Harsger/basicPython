from __future__ import print_function
import sys , os , copy , string
import numpy as np
import ROOT
from ROOT import TFile , TH1 , TH2 , TIter , TKey

cpp_code_readhist = """

class ReadHist{

    public :

        vector< double > entries1D ;
        vector< double > edges1D ;

        vector< vector<double> > entries2D ;
        vector< vector<double> > edges2D ;
        
        ReadHist(){} ;

        void get1Dentries( TH1 * hist ){
            entries1D.clear() ;
            edges1D.clear() ;
            unsigned int nbins = (unsigned int)hist->GetNbinsX() + 2 ;
            for(unsigned int b=0; b<nbins; b++){
                entries1D.push_back( hist->GetBinContent( b ) ) ; 
                if( b == 0 ) continue ;
                edges1D.push_back( hist->GetBinLowEdge( b ) ) ;
            }
        }

        void get2Dentries( TH2 * hist ){
            entries2D.clear() ;
            edges2D.clear() ;
            unsigned int nbins[2] = { 
                                        (unsigned int)hist->GetNbinsX() + 2 , 
                                        (unsigned int)hist->GetNbinsY() + 2 
                                    } ;
            vector<double> entriesDummy , edgesDummy ;
            for(unsigned int y=0; y<nbins[1]; y++){
                for(unsigned int x=0; x<nbins[0]; x++){
                    entriesDummy.push_back( hist->GetBinContent( x , y ) ) ; 
                    if( y != 0 ||  x < 1 ) continue ;
                    edgesDummy.push_back( 
                                            hist->GetXaxis()->GetBinLowEdge( x ) 
                                        ) ;
                }
                entries2D.push_back( entriesDummy ) ;
                entriesDummy.clear() ;
                if( y == 0 ){
                    edges2D.push_back( edgesDummy ) ;
                    edgesDummy.clear() ;
                    continue ;
                }
                edgesDummy.push_back( hist->GetYaxis()->GetBinLowEdge( y ) ) ;
            }
            edges2D.push_back( edgesDummy ) ;
        }

} ;

"""

def onlyCommonCharacters( word ) :
    noSpecial = True
    for c in word :
        if( 
            not c in string.ascii_letters
            and
            not c in string.digits
            and
            c != "_"
        ) :
            noSpecial = False
            break
    return noSpecial

def getFilename( fullname ) :
    filename = copy.deepcopy( fullname )
    if '/' in filename :
        if filename[-1] == '/' :
            filename = filename[0:len(filename)-1]
        filename = filename[ filename.rfind('/')+1 : len(filename) ]
    if '.' in filename :
        filename = filename[ 0 : filename.rfind('.') ]
    return filename

def getFileList( directory , ending  ) :
    filelist = []
    directoryList = os.listdir( directory )
    for filename in directoryList :
        if( 
            filename.endswith( str(ending) ) 
            and
            onlyCommonCharacters( getFilename( filename ) )
        ) : 
            filelist.append( filename )
    return filelist

def createHistFromArray( inputArray , histname ) :
    hist = ROOT.TH1D()
    if len(inputArray.shape) == 1 :
        nbins = inputArray.shape[0]
        hist = ROOT.TH1D( 
                            histname , histname , 
                            nbins , -0.5 , nbins-0.5 
                        )
        hist.FillN( nbins , np.arange(nbins) , inputArray )
    elif len(inputArray.shape) == 2 :
        nbins = [ inputArray.shape[0] , inputArray.shape[1] ]
        hist.Delete()
        hist = ROOT.TH2D(
                            histname , histname ,
                            nbins[0] , -0.5 , nbins[0]-0.5 ,
                            nbins[1] , -0.5 , nbins[1]-0.5 
                        )
        hist.FillN(
                    inputArray.size ,
                    np.transpose(
                                    np.tile( 
                                                np.arange(nbins[0]) , 
                                                ( nbins[1] , 1 )
                                            )
                                ).astype(float).flatten() ,
                    np.tile( 
                                np.arange(nbins[1]) , 
                                ( nbins[0] , 1 )
                            ).astype(float).flatten() , 
                    inputArray.astype(float).flatten()
                )
    elif len(inputArray.shape) == 3 :
        hist = ROOT.TObjArray()
        hist.SetName(histname)
        hist.SetOwner(True)
        lowestDimension = min( inputArray.shape )
        dimensionIndex  = inputArray.shape.index( lowestDimension )
        for i in range(lowestDimension) :
            hist.Add( 
                        createHistFromArray( 
                            np.take( inputArray , i , axis=dimensionIndex ) , 
                            str(histname)+"_"+str(i) 
                        ) 
                    )
    elif len(inputArray.shape) > 3 :
        hist = createHistFromArray( inputArray.flatten() , histname )
    return hist

def positionsFromEdges( edges ) :
    if len(edges.shape) != 1 :
        return edges
    entries = edges.shape[0]
    return np.append( 
                        [ ( edges[0] * 3. - edges[1] ) * 0.5 ] ,
                        np.append(
                            ( edges[1:] + edges[ 0 : entries-1 ] ) * 0.5 , 
                            [
                                (
                                    edges[entries-1] * 3. 
                                    - 
                                    edges[entries-2] 
                                ) * 0.5
                            ]
                        )
                    )

def create1DhistFromArray( inputArray , histname , edges ) :
    hist = ROOT.TH1D()
    if(
        len(inputArray.shape) != 1
        or
        len(edges.shape) != 1
        or
        inputArray.shape[0]-1 != edges.shape[0]
    ) :
        return hist
    hist = ROOT.TH1D( histname , histname , edges.shape[0]-1 , edges )
    positions = positionsFromEdges( edges )
    hist.FillN( inputArray.size , positions , inputArray )
    return hist

def create2DhistFromArray( inputArray , histname , edgesX , edgesY ) :
    hist = ROOT.TH2D()
    if(
        len(inputArray.shape) != 2
        or
        len(edgesX.shape) != 1
        or
        len(edgesY.shape) != 1
        or
        inputArray.shape[0]-1 != edgesX.shape[0]
        or
        inputArray.shape[1]-1 != edgesY.shape[0]
    ) :
        return hist
    hist = ROOT.TH2D( 
                        histname , histname , 
                        edgesX.shape[0]-1 , edgesX ,
                        edgesY.shape[0]-1 , edgesY
                    )
    positionsX = positionsFromEdges( edgesX )
    positionsY = positionsFromEdges( edgesY )
    hist.FillN( 
                inputArray.size , 
                np.tile( 
                    positionsX , 
                    ( inputArray.shape[1] , 1 )
                ).astype(float).flatten() ,
                np.transpose(
                    np.tile( 
                        positionsY , 
                        ( inputArray.shape[0] , 1 )
                    )
                ).astype(float).flatten() , 
                inputArray.astype(float).flatten() 
            )
    return hist

def main(argv) :
    global cpp_code_readhist
    if len(argv) < 1 :
        print(" ERROR : no input specified ")
        sys.exit(1)
    pathORfilename = argv[0]
    filelist = []
    filetypes = [ ".root" , ".npy" , ".npz" ]
    if len(argv) > 1 and argv[1] in filetypes :
        filetypes = [ argv[1] ]
    combine = True
    if len(argv) > 2 and "separate" in argv[2] :
        combine = False
    foundType = "path"
    outname = ""
    for t in filetypes :
        if pathORfilename.endswith( t ) :
            foundType = t
            outname = getFilename( pathORfilename )
            filelist.append( str(outname)+str(t) )
            break
    if foundType == "path" :
        for t in filetypes :
            currentList = getFileList( pathORfilename , t )
            if len(filelist) < len(currentList) :
                filelist = currentList
                foundType = t
        if len(filelist) < 1 :
            print(" ERROR : no data-files found ")
            sys.exit(2)
        elif len(filelist) == 1 :
            outname = getFilename( filelist[0] )
            combine = False
        else :
            outname = getFilename( pathORfilename )
    else :
        combine = False
    if len(outname) < 1 :
        outname = "defaultConverterOutput"
    if foundType == ".root" :
        outname += ".npz"
        ROOT.gInterpreter.ProcessLine( cpp_code_readhist )
        histReader = ROOT.ReadHist()
        dataTOwrite = {}
    elif ".np" in foundType :
        outname += ".root"
        if combine :
            outfile = TFile( outname , "RECREATE" )
    for f in filelist :
        print( str(f) , end="" )
        readname = pathORfilename
        if not readname.endswith( f ) :
            if not readname.endswith( '/' ) :
                readname += '/'
            readname += f
        if foundType == ".root" :
            print("")
            infile = TFile( readname , "READ" )
            if infile == None :
                continue
            if not combine :
                dataTOwrite = {}
            ROOT.gInterpreter.ProcessLine( "gErrorIgnoreLevel = 3001 ;" )
            for key in infile.GetListOfKeys() :
                rootObject = key.ReadObj()
                if rootObject == None :
                    continue
                if( 
                    not rootObject.ClassName().startswith( "TH1" )
                    and
                    not rootObject.ClassName().startswith( "TH2" )
                ) :
                    continue
                if not onlyCommonCharacters( rootObject.GetName() ) :
                    continue
                print( 
                        " "   + str( rootObject.ClassName() ) +
                        " * " + str( rootObject.GetName()   ) 
                    )
                histname = rootObject.GetName()
                if combine :
                    histname = f.replace( ".root" , "_" ) + histname
                if rootObject.ClassName().startswith( "TH1" ) :
                    histReader.get1Dentries( rootObject )
                    dataTOwrite[histname] = np.array( histReader.entries1D )
                    histname += "_edges"
                    dataTOwrite[histname] = np.array( histReader.edges1D )
                elif rootObject.ClassName().startswith( "TH2" ) :
                    histReader.get2Dentries( rootObject )
                    dataTOwrite[histname] = np.asarray( histReader.entries2D )
                    histname += "_edges"
                    writename = str(histname)+"X"
                    dataTOwrite[writename] = np.array( histReader.edges2D[0] )
                    writename = str(histname)+"Y"
                    dataTOwrite[writename] = np.array( histReader.edges2D[1] )
            if not combine :
                np.savez( f.replace( ".root" , ".npz" ) , **dataTOwrite )
        elif foundType == ".npy" :
            inputArray = np.load( readname )
            print( 
                    " : " + str( inputArray.dtype ) + 
                    " : " + str( inputArray.shape ) ,
                    end=""
                )
            if 1 in inputArray.shape :
                inputArray = inputArray.squeeze()
                print( " > " + str( inputArray.shape ) )
            else :
                print("")
            histname = f.replace(".npy","")
            if not combine :
                histname = "hist"
            hist = createHistFromArray( inputArray , histname )
            if hist.GetName() != histname :
                hist.Delete()
                continue
            if not combine :
                outfile = TFile( 
                                    f.replace( ".npy" , ".root" ) , 
                                    "RECREATE" 
                                )
            outfile.cd()
            hist.Write()
            hist.Delete()
            if not combine :
                outfile.Write()
                outfile.Close()
        elif foundType == ".npz" :
            print("")
            inputData = np.load( readname )
            histsTOwrite = ROOT.TObjArray()
            histsTOwrite.SetOwner(True)
            for name , data in inputData.items() :
                if( 
                    name.endswith("_edges" ) or 
                    name.endswith("_edgesX") or 
                    name.endswith("_edgesY") 
                ) :
                    continue
                print( 
                        " "   + str(name) +
                        " : " + str( data.dtype ) + 
                        " : " + str( data.shape ) ,
                        end=""
                    )
                if not onlyCommonCharacters( name ) :
                    print( " > skipped " )
                    continue
                if 1 in data.shape :
                    data = data.squeeze()
                    print( " > " + str( data.shape ) , end="" )
                histname = name
                if combine :
                    histname = f.replace(".npz","_")
                    histname += str(name)
                hist = ROOT.TH1D()
                if( 
                    len(data.shape) == 1
                    and
                    str(name)+"_edges" in inputData.keys()
                ) :
                    hist = create1DhistFromArray( 
                                                data , histname , 
                                                inputData[str(name)+"_edges"] 
                                            )
                elif(
                    len(data.shape) == 2
                    and
                    str(name)+"_edgesX" in inputData.keys()
                    and
                    str(name)+"_edgesY" in inputData.keys()
                ) :
                    hist = create2DhistFromArray( 
                                                data , histname , 
                                                inputData[str(name)+"_edgesX"] , 
                                                inputData[str(name)+"_edgesY"] 
                                            )
                if hist.GetName() != histname :
                    hist = createHistFromArray( data , histname )
                if hist.GetName() != histname :
                    hist.Delete()
                    print( " > skipped " )
                    continue
                histsTOwrite.Add( hist )
                print("")
            if not combine :
                outfile = TFile( 
                                    f.replace( ".npz" , ".root" ) , 
                                    "RECREATE" 
                                )
            outfile.cd()
            histsTOwrite.Write()
            histsTOwrite.Delete()
            if not combine :
                outfile.Write()
                outfile.Close()
                
    if combine :
        print( " = > "+str(outname) )
        if foundType == ".root" :
            np.savez( outname , **dataTOwrite )
        if ".np" in foundType :
            outfile.Write()
            outfile.Close()
    

if __name__ == "__main__":
    main(sys.argv[1:])
