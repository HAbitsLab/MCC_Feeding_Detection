import numpy as np
from myDBA_ndim import dtw_distance_ndim, dtw_distance_1d, dtw_distance_ndim_sq_win, dtw_distance_1d_sq_win
from myDBA import dtw_distance
from dtw_ndim_modified import dtw_ndim

# from dtwalign import dtw as cdtw  # WRONG OUTPUT  cannot be used for multi-dim dtw, gives erronous result


def dtw(a, b, ndim=True, squared=True):
    # if squared == True:
    
    if not ndim or (len(a.shape) == 1 and len(b.shape) == 1):
        return dtw_distance(a, b)
    else:
        return dtw_ndim(a, b, window=8)
    
    # else:
    #     if not ndim or (len(a.shape) == 1 and len(b.shape) == 1):
    #         return dtw_distance_1d(a, b)
    #     else:
    #         return dtw_distance_ndim(a, b)


if __name__ == '__main__':
    import timeit

    # a1 = np.array([1,0,0,2,1,0]) 
    # b1 = np.array([1,0,2,1,0,0]) 
    # a2 = np.array([1,0,3,2,1,0]) 
    # b2 = np.array([1,0,3,2,1,0]) 
    # print(dtw(a1, b1))
    # print(dtw(a2, b2))
    
    # a = np.array([1,0,0,0,0,0,0,2,1,0])
    # b = np.array([1,0,2,1,0,0,0,0,0,0])

    a = np.array([[1,0,0,2,1,0],[1,0,3,2,4,0]]).T
    b = np.array([[1,0,3,2,4,0],[1,0,0,2,1,0]]).T
    # b = np.array([[1,0,2,1,0,0],[1,0,3,2,1,0]]).T

    print(dtw(a, b))

