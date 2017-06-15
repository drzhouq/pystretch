import argparse
from pystretch.linear import Linear
from pystretch.nonlinear import Nonlinear
from pystretch.filter import Filter
from pystretch.custom import Custom

def parse_arguments():
    
    desc='''Description: %prog leverages GDAL and NUMPY to stretch raster images.  GDAL 1.8.0 and NUMPY 1.5.1 or greater are required. Both linear and non-linear stretches are available.'''
    
    parser = argparse.ArgumentParser(description=desc)
    
    generalOptions = parser.add_argument_group('I/O Options')
    linearStretches = parser.add_argument_group('Linear Stretches' )
    directionOptions = parser.add_argument_group('Directional Options')
    nonlinearstretches = parser.add_argument_group('Non-linear Stretches')
    filters = parser.add_argument_group('Filters')
    custom = parser.add_argument_group('Custom')
    
    generalOptions.add_argument('input_data', action='store', help='The input data set to be processed.')
    generalOptions.add_argument('--output', '-o',action='store',default='output.tif',type=str,dest='output',help='The optional output file')
    generalOptions.add_argument('--format', '-f',action='store',type=str,default='GTiff', dest="outputFormat" ,help='Any GDAL supported output format.') 
    generalOptions.add_argument('--ot', action='store', type=str, dest='dtype',default=None, help='A GDAL output format. (Byte, Int16, Float32 are likely candidates.' )
    generalOptions.add_argument('--visualize', '-z', action='store_true', default=False, dest='visualize', help='show the output histogram.')
    generalOptions.add_argument('--NDV', action='store', dest='ndv', type=float, help='Define an output NDV.  If the dataset has an NDV, this value and the intrinsic NDV are set to No Data in the output.  The output NDV is this value.')    
    generalOptions.add_argument('--scale','-s', action='store', dest='scale',nargs=2, type=str, help='Scale the data to 8-bit')
    generalOptions.add_argument('--segment', '--seg', action='store_true', default=False, dest='segment', help='Use this flag to calculate statistics per segment instead of per band.  Best for removing spatially describale systematic error.')
    
    custom.add_argument('--custom', action='store_true', default=False, dest='custom_stretch', help='Use this flag to call your own custom stretch.  You will need to code it into the custom_stretch function inside the Custom module')
    
    directionOptions.add_argument('--horizontal', '-t', action='store',type=int, dest='hint', default=1, help='The number of horizontal segments to divide the image into.  This will likely leave a small "remainder" segment at the edge of the image.')
    directionOptions.add_argument('--vertical', '-v', action='store', type=int, dest ='vint', default=1, help='The number of vertical segments to divide the image into.  This will likely leave a small "remainder" segment at the edge of the image.')
    
    linearStretches.add_argument('--std', '-d', action='store_true', dest='standard_deviation_stretch',default=False,help='Perform a standard deviation stretch with default n=2. Set "-n <float> to specify a different number of standard deviations.')
    linearStretches.add_argument('--standarddeviations','-n', action='store', type=float, dest='sigma', default=2, help='The number of standard deviations over which the stretch is performed.')
    linearStretches.add_argument('--linear', '-l', action='store_true', dest='linear_stretch', default=False, help='Perform a linear stretch.  To set clipping set "-c <integer>.')
    linearStretches.add_argument('--clip', '-c', action='store', type=float, default=0, dest='clip', help='The percentage to clip the tails of the histogram by')
    linearStretches.add_argument('--reduction',  action='store', type=float, default=0, dest='reduction', help='The percentage to reduced brightness by')
    linearStretches.add_argument('--inverse', '-i', action='store_true', default=False, dest='inverse_stretch', help='Perform an inverse stretch')
    linearStretches.add_argument('--binary', '-y', action='store_true', default=False, dest='binary_stretch', help='Performs a binary stretch')
    linearStretches.add_argument('--threshold', '--th', action='store', type=float, default='128', dest='threshold', help='The threshold value for the binary stretch.')
    linearStretches.add_argument('--hicut', action='store_true', default=False, dest='hicut_stretch', help='Set all values above the cut to a user defined value (defaults to 0)')
    linearStretches.add_argument('--lowcut', action='store_true', default=False, dest='lowcut_stretch', help='Set all vlues below the cut to a user defined value (defaults to 0)')
    linearStretches.add_argument('--cutvalue', action='store', type=float,dest='cutvalue', default=0, help = 'The cut value used with either lowcut or hicut.')
    
    nonlinearstretches.add_argument('--gamma', '-g', action='store_true', dest='gamma_stretch', default=False, help='Perform a gamma stretch')
    nonlinearstretches.add_argument('--gammavalue', '--gv', action='store', type=float, default=1.6, dest='gammavalue', help='The gamma value to be used.  Processed as 1/gamma.')
    nonlinearstretches.add_argument('--histogramequalization', '-q', action='store_true', default=False, dest='histequ_stretch', help='Perform a histogram equalization.  It is suggested that sample size be set to 1 to ensure that the entire image is processed.  Default number of bins is 128, to change this set "-b <integer number of bins>".')
    nonlinearstretches.add_argument('--bins', '-b', action='store', type=int, default=128, dest='num_bins', help='The number of bins to be used with the histogram equalization.')
    nonlinearstretches.add_argument('--log', '-r', action='store_true', dest='logrithmic_stretch', default=False, help='Performs a logrithmic stretch with default epsilon of 1.  This is most likely appropriate for images with magnitudes typically much larger than 1.  To modify epsilon use "-e <float epsilon value>".')
    nonlinearstretches.add_argument('--epsilon', '-e', action='store', type=float, default=1, dest='epsilon', help='The desired epsilon value.')
    #nonlinearstretches.add_argument('--gaussian', '-u', action='store_true', default=False, dest='gaussian_stretch', help='Performs a gaussian stretch.')
    #nonlinearstretches.add_argument('--histogrammatch', '-m', action='store_true', default=False,dest='histogram_match', help='Perform a histogram match to another image. Be sure to define the input reference histogram')
    #nonlinearstretches.add_argument('--referenceimage','--ref', action='store',dest='reference_input', help='The reference histogram to match')
    
    filters.add_argument('--laplacian', '--lap', action='store_true', default=False, dest='laplacian_filter', help='Perform a laplacian filter.')
    filters.add_argument('--hipass3', '--hi3', action='store_true', default=False, dest='hipass_filter_3x3', help='Perform a hipass filter.')
    filters.add_argument('--hipass5', '--hi5', action='store_true', default=False, dest='hipass_filter_5x5', help='Perform a hipass filter.')
    filters.add_argument('--gaussianfilter','--gf', action='store_true', default=False, dest='gaussian_filter', help='Performs a gaussian (lowpass) filter on an image')
    filters.add_argument('--gaussianhipass','--gh', action='store_true', default=False, dest='gaussian_hipass', help='Performs a gaussian hipass filter on an image')
    filters.add_argument('--meanfilter', '--mf', action='store_true', default=False, dest='mean_filter', help ='Perform mean filter.')
    filters.add_argument('--conservativefilter', '--cf', action='store_true', default=False, dest='conservative_filter', help='Perform a conservative filter.')
    filters.add_argument('--kernelsize', '-k', action='store', default=3, type=int, dest='kernel_size', help='A positive, odd, integer which is the size of the kernel to be created')
    filters.add_argument('--median', '--md', action='store_true', default=False, dest='median_filter', help='Perform a median filtering of the input image with default 3x3 kernel.  Specify -k int, where int is an odd integer for a larger kernel')
    
    return(parser.parse_args())


#This needs to get cleanup / improved.  It would be better to use the dict function in ArrayConvert.
def get_stretch(args):
    if args.linear_stretch == True:
        return Linear.linear_stretch
    elif args.standard_deviation_stretch == True:
        return Linear.standard_deviation_stretch
    elif args.inverse_stretch == True:
        return Linear.inverse_stretch
    elif args.binary_stretch == True:
        return Linear.binary_stretch
    elif args.hicut_stretch == True:
        return Linear.hicut_stretch
    elif args.lowcut_stretch == True:
        return Linear.lowcut_stretch
    elif args.gamma_stretch == True:
        return Nonlinear.gamma_stretch
    elif args.histequ_stretch == True:
        return Nonlinear.histequ_stretch
    elif args.mean_filter == True:
        return Filter.mean_filter
    elif args.median_filter == True:
        return Filter.median_filter
    elif args.laplacian_filter == True:
        return Filter.laplacian_filter
    elif args.hipass_filter_3x3 == True:
        return Filter.hipass_filter_3x3
    elif args.hipass_filter_5x5 == True:
        return Filter.hipass_filter_5x5
    elif args.gaussian_filter == True:
        return Filter.gaussian_filter
    elif args.gaussian_hipass == True:
        return Filter.gaussian_hipass
    elif args.conservative_filter == True:
        return Filter.conservative_filter
    elif args.custom_stretch == True:
        return Custom.custom_stretch
        
            
