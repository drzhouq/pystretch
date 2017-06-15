#!/usr/bin/python

#Internal imports
from pystretch.core import GdalIO, ArrayConvert, OptParse, Stats, Timer
from pystretch.masks import Segment

#Debugging imports
#import profile
#Core imports

import multiprocessing
from contextlib import closing
import sys
import time
import gc

#External imports
try:
    from osgeo import gdal
    from osgeo.gdalconst import *
    version_num = int(gdal.VersionInfo('VERSION_NUM'))
    if version_num <1800 :
        print 'ERROR: Python bindings of GDAL version 1.8.0 or later required'
        raise
    else:
        pass
except ImportError:
    print "GDAL and the GDAL python bindings must be installed."
    raise

try:
    import numpy
except ImportError:
    print "NumPY must be installed."
    raise

try:
    import scipy
except ImportError:
    print "Some functionality will not work without scipy installed."

    
def main(args):

    starttime = Timer.starttimer()
    #Cache thrashing is common when working with large files, we help alleviate misses by setting a larger than normal cache.  1GB
    #gdal.SetCacheMax(1073741824)
    gdal.SetCacheMax(2147483648)
    
    #Check for input
    if not args:
        print "\nERROR: You must supply an input data set.\n"
        sys.exit(0)
    
    #Get stretch type
    stretch = OptParse.get_stretch(args)
    
    #Get some info about the machine for multiprocessing
    cores = multiprocessing.cpu_count()
    cores *= 2
    print "Processing on %i cores." %cores
    
    #Load the input dataset using the GdalIO class and get / set the output datatype.
    dataset = GdalIO.GdalIO(args.input_data)
    raster = dataset.load()

    #Default is none, unless user specified
    if args.dtype == None:
        dtype = gdal.GetDataTypeName(raster.GetRasterBand(1).DataType)
    else:
        dtype=args.dtype
    
    #Create an output if the stretch is written to disk
    xsize, ysize, bands, projection, geotransform = dataset.info(raster)
    output = dataset.create_output("",args.output,xsize,ysize,bands,projection, geotransform, gdal.GetDataTypeByName(dtype))

    #Segment the image to handle either RAM constraints or selective processing
    segments = Segment.segment_image(xsize,ysize,args.vint, args.hint)

    for b in xrange(bands):
        band = raster.GetRasterBand(b+1)
        bandstats = Stats.get_band_stats(band, args)
        
        for key in bandstats.iterkeys():
            #print (key, bandstats[key])
            if key == 'bandmax':
                args.bandmax = bandstats['bandmax']
            elif key == 'bandstd':
                args.bandstd = bandstats['bandstd']
            elif key == 'bandmin':
                args.bandmin = bandstats['bandmin']
            elif key == 'ndv_band':
                args.ndv_band = bandstats['ndv_band']
            elif key == 'bandmean':
                args.bandmean = bandstats['bandmean']
#            elif key == 'lowerbound':
#                args.lowerbound = bandstats['lowerbound']
#            elif key == 'upperbound':
#                args.upperbound = bandstats['upperbound']
#        args.reduction = 0.1
        #Get the size of the segments to be manipulated
        piecenumber = 1
        for chunk in segments:
            
            print "Image segmented.  Processing segment %i of %i" %(piecenumber, len(segments))
            piecenumber += 1
            (xstart, ystart, intervalx, intervaly) = chunk
            
            array = band.ReadAsArray(xstart, ystart, intervalx, intervaly).astype(numpy.float32)

            if args.ndv_band != None:
                array = numpy.ma.masked_values(array, args.ndv_band, copy=False)
            elif args.ndv != None:
                array = numpy.ma.masked_values(array, args.ndv, copy=False)
            
            if 'stretch' in stretch.__name__:
                array = Stats.normalize(array, args.bandmin, args.bandmax, dtype)
                args.normalized = True

                #print(args)
            if args.clip > 0:  
                stats = Stats.get_array_percentile(array, args.clip) 
                args.lowerbound = stats['lowerbound']
                args.upperbound = stats['upperbound']
                
            #If the user wants to calc stats per segment:
            if args.segment == True:  
                stats = Stats.get_array_stats(array, stretch) 
                for key in stats.iterkeys():
                    args[key] = stats[key]
            #Otherwise use the stats per band for each segment
            else:
                args.mean = args.bandmean
                args.maximum = args.bandmax
                args.minimum = args.bandmin
                args.standard_deviation = args.bandstd
            
            y,x = array.shape
            
            #Calculate the hist and cdf if we need it.  This way we do not calc it per core.
            if args.histequ_stretch == True:
                cdf, bins = Stats.gethist_cdf(array,args.num_bins)
                args.cdf = cdf
                args.bins = bins
            

            #Fill the masked values with NaN to get to a shared array
            if args.ndv != None:
                array = array.filled(numpy.nan)
            
            #Create an ctypes array
            init(ArrayConvert.SharedMemArray(array))
            options = args
            step = y // cores
            jobs = []
            if step != 0:
                for i in range(0,y,step):        
                    p = multiprocessing.Process(target=stretch,args= (shared_arr,slice(i, i+step),args))
                    jobs.append(p)
                    
                for job in jobs:
                    job.start()
                    del job
                for job in jobs:
                    job.join()
                    del job
            
            #Return the array to the proper data range and write it out.  Scale if that is what the user wants
            #if args.histequ_stretch or args.gamma_stretch== True:
            #    pass
            #elif 'filter' in stretch.__name__:
            #    pass
            #else:
            if args.normalized == True:
                Stats.denorm(shared_arr.asarray(), dtype, args)

            if args.scale != None:
                Stats.scale(shared_arr.asarray(), args)
                
            #If their are NaN in the array replace them with the dataset no data value
            Stats.setnodata(shared_arr, args.ndv)

            #Write the output
            output.GetRasterBand(b+1).WriteArray(shared_arr.asarray(), xstart,ystart)            
            #Manually cleanup to stop memory leaks.
            del array, jobs, shared_arr.data
            try: 
                del stats
            except:
                pass
            del globals()['shared_arr']
            gc.collect()
            
            if args.ndv != None:
                output.GetRasterBand(b+1).SetNoDataValue(float(args.ndv))
            elif args.ndv_band != None:
                output.GetRasterBand(b+1).SetNoDataValue(float(args.ndv_band))
                
                
    if args.visualize == True:
        Plot.show_hist(shared_arr.asarray())
    
    Timer.totaltime(starttime)
    
    #Close up
    dataset = None
    output = None
    gc.collect()

def init(shared_arr_):
    global shared_arr
    shared_arr = shared_arr_ # must be inhereted, not passed as an argument global array

if __name__ == '__main__':
    multiprocessing.freeze_support()
    #If the script is run via the command line we start here, otherwise start in main.
    args = OptParse.parse_arguments()
    gdal.SetConfigOption('CPL_DEBUG', 'ON')

    main(args)
    
