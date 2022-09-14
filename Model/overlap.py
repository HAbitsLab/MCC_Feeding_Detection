import numpy as np

def overlap_len(arr_1, arr_2):
    '''
    Calculate total length of overlap between two arrays.
    
    :param ndarray arr_1: 1st start and end time of gestures (shape: Nx2).
    :param ndarray arr_2: 2nd start and end time of gestures (shape: Nx2).

    :return float result: overlapped length of time between two arrays.
    '''
    result = 0
    
    # interate the first array
    for i in range(arr_1.shape[0]):
        a_s = arr_1[i][0] # start
        a_e = arr_1[i][1] # end
        
        # interate the second array
        for j in range(arr_2.shape[0]):
            b_s = arr_2[j][0] # start
            b_e = arr_2[j][1] # end
            
            if ((a_s < b_e) & (b_s < a_e)): # check if overlap
                total = max(a_s,a_e,b_s,b_e) - min(a_s,a_e,b_s,b_e)
                overlap = (a_e - a_s) + (b_e - b_s) - total
                result = result + overlap # update total overlap 
                break                 
    return result

def overlap_perc(arr_1, arr_2):
    '''
    Calculate total length of overlap between one ndarray and a list of ndarrays.
    
    :param ndarray arr_1: 1st start and end time of a gesture (shape: 1x2).
    :param ndarray arr_2: 2nd start and end time of all gestures (shape: Nx2).

    :return float result: overlapped length of time between two arrays.
    '''
    overlap = 0
    a_s = arr_1[0] # start
    a_e = arr_1[1] # end

    # interate the second array
    for j in range(arr_2.shape[0]):
        b_s = arr_2[j][0] # start
        b_e = arr_2[j][1] # end

        if ((a_s < b_e) & (b_s < a_e)): # check if overlap
            total = max(a_s,a_e,b_s,b_e) - min(a_s,a_e,b_s,b_e)
            overlap = (a_e - a_s) + (b_e - b_s) - total
            result = (overlap)/(a_e - a_s)
            return result
            
    return (overlap)/(a_e - a_s)

def combine_overlap(arr_1, arr_2):
    '''
    Combine the overlapped segments from both arrays into combined segements.
    Orginal overlapped segements are removed, non-overlapped segemnts are retained.
    
    :param ndarray arr_1: 1st start and end time of gestures (shape: Nx2).
    :param ndarray arr_2: 2nd start and end time of gestures (shape: Nx2).

    :return float result: combined array with overlapped and non-overlapped segments from two arrays.
    '''
    result = []
    overlap_idx_1 = []
    overlap_idx_2 = []
    
    # interate the first array
    for i in range(arr_1.shape[0]):
        a_s = arr_1[i][0] # start
        a_e = arr_1[i][1] # end
        
        # interate the second array
        for j in range(arr_2.shape[0]):
            b_s = arr_2[j][0] # start
            b_e = arr_2[j][1] # end
            
            if ((a_s < b_e) & (b_s < a_e)): # check if overlap
                result.append(np.array([min(a_s,a_e,b_s,b_e),max(a_s,a_e,b_s,b_e)])) # add the combined segement
                overlap_idx_1.append(i) # get overlapped 1st segment
                overlap_idx_2.append(j) # get overlapped 2nd segment
                break
    
    # delete original overlapped segments (i and j) from both arrays    
    for each in np.delete(arr_1, overlap_idx_1, axis=0):
        result.append(each)
    for each in np.delete(arr_2, overlap_idx_2, axis=0):
        result.append(each)          
    return np.array(result)

def overlap_seg(arr_1, arr_2):
    '''
    Calculate total length of overlap between two arrays.
    
    :param ndarray arr_1: 1st start and end time of gestures (shape: Nx2).
    :param ndarray arr_2: 2nd start and end time of gestures (shape: Nx2).

    :return ndarray result: intersect start and end time of two arrays.
    '''
    result = []
    
    # interate the first array
    for i in range(arr_1.shape[0]):
        a_s = arr_1[i][0] # start
        a_e = arr_1[i][1] # end
        
        # interate the second array
        for j in range(arr_2.shape[0]):
            b_s = arr_2[j][0] # start
            b_e = arr_2[j][1] # end
            
            if ((a_s < b_e) & (b_s < a_e)): # check if overlap
                all_time = [a_s, a_e, b_s, b_e]
                all_time.sort()
                result.append([all_time[1],all_time[2]]) # update total overlap 
                break                 
    return np.array(result)

def mergeIntervals(arr):    
    '''
    Sorting based on the increasing order of the start intervals.
    
    :param ndarray arr: 1st start and end time of gestures (shape: Nx2).

    :return ndarray: combined overlapped start and end time of two arrays.
    '''

    arr.sort(key = lambda x: x[0])

    # array to hold the merged intervals
    m = []
    s = -10000
    max = -100000
    for i in range(len(arr)):
        a = arr[i]
        if a[0] > max:
            if i != 0:
                m.append([s,max])
            max = a[1]
            s = a[0]
        else:
            if a[1] >= max:
                max = a[1]

    if max != -100000 and [s, max] not in m:
        m.append([s, max])
    return m

def combine_continous(arr):
    '''
    Combine start and end of continous time inside one array.
    
    :param ndarray arr: 1st start and end time of gestures (shape: Nx2).

    :return ndarray: combined continous start and end time of two arrays.
    '''

    arr = arr[arr[:, 0].argsort()]
    idx_1 = 0
    idx_2 = 0
    idx_3 = idx_2 + 1
    new = []

    while(idx_3 < arr.shape[0]):
        if(arr[idx_2][1] == arr[idx_3][0]): #continue
            idx_3 = idx_3 + 1
            idx_2 = idx_2 + 1
        else:
            new.append([arr[idx_1][0], arr[idx_2][1]])
            idx_1 = idx_3
            idx_2 = idx_2 + 1
            idx_3 = idx_3 + 1
    new.append(list(arr[arr.shape[0]-1]))
    return(np.array(new))