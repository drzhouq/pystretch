import numpy


def linear_stretch(shared_array, i,args):

    clip = args.clip


    if args.normalized == True:
        maximum, minimum = 1, 0
    else:
        maximum, minimum = args.maximum, args.minimum

    #newmin = minimum * ((100.0+clip)/100.0)

    #newmax = maximum * ((100.0-clip)/100.0)

    arr = shared_array.asarray()
    newmin = args.lowerbound 
    newmax = args.upperbound 
    #print (newmax, newmin, args.reduction)
    #print (minimum, maximum, newmin, newmax)
    #arr[i] -= newmin
    #since the arr is already normalized, the maxium and minimum would be 1 and 0
    arr[i] =(arr[i]-newmin)*((maximum - minimum)/(newmax - newmin))+minimum - args.reduction*(maximum - minimum)
        
    low_value_index = arr[i] < minimum
    arr[i][low_value_index] = minimum
    high_value_index = arr[i] > maximum 
    arr[i][high_value_index] =  maximum
  # reference to http://homepages.inf.ed.ac.uk/rbf/HIPR2/stretch.htm 
    #arr[i] =arr[i]*((newmax - newmin)/(maximum-minimum)) + newmin


def standard_deviation_stretch(shared_array, i,args):

    array_mean = args.mean

    array_standard_deviation = args.standard_deviation

    sigma = args.sigma

    newmin = array_mean - (array_standard_deviation * sigma)

    newmax = array_mean + (array_standard_deviation * sigma)

    arr = shared_array.asarray()

    arr[i] -= newmin

    arr[i] *= 1.0/(newmax-newmin)

    

def inverse_stretch(shared_array, i, args):

    maximum = args.maximum

    arr = shared_array.asarray()

    arr[i] -= maximum

    arr[i] = abs(arr[i])



def binary_stretch(shared_array, i, args):

    threshold = args.threshold

    #Normalize the threshold value because we normalized our data

    threshold = (threshold - args.bandmin)/(args.bandmax-args.bandmin)

    arr = shared_array.asarray()

    low_value_index = arr[i] < threshold

    arr[i][low_value_index] = 0.0

    high_value_index = arr[i] > threshold

    arr[i][high_value_index] = 255.0

    

def hicut_stretch(shared_array, i, args):

    threshold = args.cutvalue

    threshold = (threshold - args.bandmin)/(args.bandmax-args.bandmin)

    arr = shared_array.asarray()

    high_value_index = arr[i] > threshold

    arr[i][high_value_index] = args.cutvalue

    

def lowcut_stretch(shared_array, i, args):

    threshold = args.cutvalue

    threshold = (threshold - args.bandmin)/(args.bandmax-args.bandmin)

    arr = shared_array.asarray()

    low_value_index = arr[i] < threshold

    arr[i][low_value_index] = args.cutvalue
