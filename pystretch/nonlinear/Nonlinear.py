import numpy
import scipy.stats

def gamma_stretch(shared_array, i, args):
    gammavalue = args.gammavalue
    bandmax = args.bandmax
    print(bandmax, gammavalue)
    arr = shared_array.asarray()
    arr[i] **= (1.0/gammavalue)
    arr[i] *= bandmax

def histequ_stretch(shared_array, i, args):
    cdf = args.cdf
    bins = args.bins
    arr = shared_array.asarray()
    shape = arr[i].shape
    #interpolate
    arr[i] = numpy.interp(arr[i],bins[:-1],cdf)
    #reshape
    arr[i] = arr[i].reshape(shape)

def logarithmic_stretch(shared_array, i, args):
    maximum = args.maximum
    epsilon = args.epsilon
    #Find the scaling constant
    c = 255/(numpy.log10(1+abs(maximum)))
    arr = shared_arr.asarray()
    arr[i] = c * numpy.log10(epsilon + abs(arr[i]))
    
def fft_pass(shared_array, i, args):
    pass
