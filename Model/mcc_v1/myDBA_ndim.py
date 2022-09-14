''' 

/******************************************************************************* 

* Modified based on "Copyright (C) 2018 Francois Petitjean" by Shibo 

* 

* This program is free software: you can redistribute it and/or modify 

* it under the terms of the GNU General Public License as published by 

* the Free Software Foundation, version 3 of the License. 

* 

* This program is distributed in the hope that it will be useful, 

* but WITHOUT ANY WARRANTY; without even the implied warranty of 

* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 

* GNU General Public License for more details. 

* 

* You should have received a copy of the GNU General Public License 

* along with this program.  If not, see <http://www.gnu.org/licenses/>. 

******************************************************************************/ 

''' 

from __future__ import division 

import numpy as np 

import matplotlib.pyplot as plt 

from functools import reduce 

import timeit 

from numba import jit, prange 

import os, sys 

import matplotlib.pyplot as plt 

  

# from util_data import img_norm 

  

np.random.seed(1) 

  

  

# no speed up effect, not better than np.subtract.outer  

@jit(nopython=True, parallel=True, fastmath=True) 

def subtract_outer(x,y): 

    z=np.empty((len(x), len(x))) 

    for i in prange(x.shape[0]): 

        for j in prange(x.shape[0]): 

            z[i,j] = x[i]-y[j] 

    return z 

  

  

@jit(nopython=True, parallel=True, nogil=True) 

def dtw_distance_ndim_set(dataset1, dataset2): 

    """ 

    Computes the dataset DTW distance matrix using multiprocessing. 

  

    Args: 

        dataset1: timeseries dataset of shape [N1, T1] 

        dataset2: timeseries dataset of shape [N2, T2] 

  

    Returns: 

        Distance matrix of shape [N1, N2] 

    """ 

    n1 = dataset1.shape[0] 

    n2 = dataset2.shape[0] 

    dist = np.empty((n1, n2), dtype=np.float64) 

  

    for i in prange(n1): 

        for j in prange(n2): 

            # dist[i][j] = dtw_distance_ndim(dataset1[i], dataset2[j]) 

            dist[i][j] = dtw_distance_ndim_sq_win(dataset1[i], dataset2[j]) 

  

    return dist 

  

  

@jit(nopython=True, cache=True) 

def dtw_distance_1d_sq_win(series1, series2, w=np.inf): 

    """ 

    Returns the DTW similarity distance between two 1-D 

    timeseries numpy arrays. 

  

    Args: 

        series1, series2 : array of shape [n_timepoints] 

            Two arrays containing n_samples of timeseries data 

            whose DTW distance between each sample of A and B 

            will be compared. 

  

    Returns: 

        DTW distance between A and B 

    """ 

    l1 = series1.shape[0] 

    l2 = series2.shape[0] 

    # E = np.empty((l1, l2)) 

    E = np.full((l1, l2), np.inf) 

  

    # Fill First Cell 

    v = series1[0] - series2[0] 

    # E[0][0] = np.absolute(v) 

    E[0][0] = v * v 

  

    # Fill First Column 

    for i in range(1, l1): 

        # v = series1[i] - series2[0] 

        # E[i][0] = E[i - 1][0] + np.absolute(v) 

        if i < w + 1: 

            v = series1[i] - series2[0] 

            E[i][0] = E[i - 1][0] + v * v 

  

    # Fill First Row 

    for i in range(1, l2): 

        # v = series1[0] - series2[i] 

        # E[0][i] = E[0][i - 1] + np.absolute(v) 

        if i < w + 1: 

            v = series1[0] - series2[i] 

            E[0][i] = E[0][i - 1] + v * v 

  

    for i in range(1, l1): 

        for j in range(1, l2): 

            if (j < (i + w + 1)) and (j > (i + w - l2 - 1)): 

                v = series1[i] - series2[j] 

                # v = np.absolute(v) 

                v = v * v 

                v1 = E[i - 1][j] 

                v2 = E[i - 1][j - 1] 

                v3 = E[i][j - 1] 

  

                if v1 <= v2 and v1 <= v3: 

                    E[i][j] = v1 + v 

                elif v2 <= v1 and v2 <= v3: 

                    E[i][j] = v2 + v 

                else: 

                    E[i][j] = v3 + v 

  

    return np.sqrt(E[-1][-1]) 

  

  

# @jit(nopython=True, cache=True) 

# def dtw_distance_ndim_sq_win(series1, series2, w=np.inf): 

#     """ 

#     Returns the DTW similarity distance between two 1-D 

#     timeseries numpy arrays. 

  

#     Args: 

#         series1, series2 : array of shape [n_timepoints] 

#             Two arrays containing n_samples of timeseries data 

#             whose DTW distance between each sample of A and B 

#             will be compared. 

  

#     Returns: 

#         DTW distance between A and B 

#     """ 

#     l1 = series1.shape[0] 

#     l2 = series2.shape[0] 

#     # E = np.empty((l1, l2)) 

#     E = np.full((l1, l2), np.inf) 

  

#     # Fill First Cell 

#     v = series1[0] - series2[0] 

#     E[0][0] = np.dot(v, v) 

  

#     # Fill First Column 

#     for i in prange(1, l1): 

#         v = series1[i] - series2[0] 

#         E[i][0] = E[i - 1][0] + np.dot(v, v) 

  

#     # Fill First Row 

#     for i in prange(1, l2): 

#         v = series1[0] - series2[i] 

#         E[0][i] = E[0][i - 1] + np.dot(v, v) 

  

#     for i in prange(1, l1): 

#         for j in prange(1, l2): 

#             v = series1[i] - series2[j] 

#             v = np.dot(v, v) 

  

#             v1 = E[i - 1][j] 

#             v2 = E[i - 1][j - 1] 

#             v3 = E[i][j - 1] 

  

#             if v1 <= v2 and v1 <= v3: 

#                 E[i][j] = v1 + v 

#             elif v2 <= v1 and v2 <= v3: 

#                 E[i][j] = v2 + v 

#             else: 

#                 E[i][j] = v3 + v 

  

#     return np.sqrt(E[-1][-1]) 

  

@jit(nopython=True, cache=True) 

def dtw_distance_ndim_sq_win(series1, series2, w=np.inf): 

    """ 

    Returns the DTW similarity distance between two 1-D 

    timeseries numpy arrays. 

  

    Args: 

        series1, series2 : array of shape [n_timepoints] 

            Two arrays containing n_samples of timeseries data 

            whose DTW distance between each sample of A and B 

            will be compared. 

  

    Returns: 

        DTW distance between A and B 

    """ 

    l1 = series1.shape[0] 

    l2 = series2.shape[0] 

    # E = np.empty((l1, l2)) 

    E = np.full((l1, l2), np.inf) 

  

    # Fill First Cell 

    v = series1[0] - series2[0] 

    E[0][0] = np.dot(v, v) 

  

    # Fill First Column 

    for i in prange(1, l1): 

        v = series1[i] - series2[0] 

        E[i][0] = E[i - 1][0] + np.dot(v, v) 

  

    # Fill First Row 

    for i in prange(1, l2): 

        v = series1[0] - series2[i] 

        E[0][i] = E[0][i - 1] + np.dot(v, v) 

  

    for i in prange(1, l1): 

        for j in prange(1, l2): 

            v = series1[i] - series2[j] 

            v = np.dot(v, v) 

  

            v1 = E[i - 1][j] 

            v2 = E[i - 1][j - 1] 

            v3 = E[i][j - 1] 

  

            if v1 <= v2 and v1 <= v3: 

                E[i][j] = v1 + v 

            elif v2 <= v1 and v2 <= v3: 

                E[i][j] = v2 + v 

            else: 

                E[i][j] = v3 + v 

  

    return np.sqrt(E[-1][-1]) 

  

  

@jit(nopython=True, cache=True) 

def dtw_distance_1d(series1, series2): 

    """ 

    Returns the DTW similarity distance between two 1-D 

    timeseries numpy arrays. 

  

    Args: 

        series1, series2 : array of shape [n_timepoints] 

            Two arrays containing n_samples of timeseries data 

            whose DTW distance between each sample of A and B 

            will be compared. 

  

    Returns: 

        DTW distance between A and B 

    """ 

    l1 = series1.shape[0] 

    l2 = series2.shape[0] 

    E = np.empty((l1, l2)) 

  

    # Fill First Cell 

    v = series1[0] - series2[0] 

    E[0][0] = np.absolute(v) 

  

    # Fill First Column 

    for i in range(1, l1): 

        v = series1[i] - series2[0] 

        E[i][0] = E[i - 1][0] + np.absolute(v) 

  

    # Fill First Row 

    for i in range(1, l2): 

        v = series1[0] - series2[i] 

        E[0][i] = E[0][i - 1] + np.absolute(v) 

  

    for i in range(1, l1): 

        for j in range(1, l2): 

            v = series1[i] - series2[j] 

            v = np.absolute(v) 

  

            v1 = E[i - 1][j] 

            v2 = E[i - 1][j - 1] 

            v3 = E[i][j - 1] 

  

            if v1 <= v2 and v1 <= v3: 

                E[i][j] = v1 + v 

            elif v2 <= v1 and v2 <= v3: 

                E[i][j] = v2 + v 

            else: 

                E[i][j] = v3 + v 

  

    return np.sqrt(E[-1][-1]) 

  

  

@jit(nopython=True, cache=True) 

def dtw_distance_ndim(series1, series2): 

    """ 

    Returns the DTW similarity distance between two 1-D 

    timeseries numpy arrays. 

  

    Args: 

        series1, series2 : array of shape [n_timepoints] 

            Two arrays containing n_samples of timeseries data 

            whose DTW distance between each sample of A and B 

            will be compared. 

  

    Returns: 

        DTW distance between A and B 

    """ 

    l1 = series1.shape[0] 

    l2 = series2.shape[0] 

    E = np.empty((l1, l2)) 

  

    # Fill First Cell 

    v = series1[0] - series2[0] 

    E[0][0] = np.sqrt(np.dot(v, v)) 

  

    # Fill First Column 

    for i in prange(1, l1): 

        v = series1[i] - series2[0] 

        E[i][0] = E[i - 1][0] + np.sqrt(np.dot(v, v)) 

  

    # Fill First Row 

    for i in prange(1, l2): 

        v = series1[0] - series2[i] 

        E[0][i] = E[0][i - 1] + np.sqrt(np.dot(v, v)) 

  

    for i in prange(1, l1): 

        for j in prange(1, l2): 

            v = series1[i] - series2[j] 

            v = np.sqrt(np.dot(v, v)) 

  

            v1 = E[i - 1][j] 

            v2 = E[i - 1][j - 1] 

            v3 = E[i][j - 1] 

  

            if v1 <= v2 and v1 <= v3: 

                E[i][j] = v1 + v 

            elif v2 <= v1 and v2 <= v3: 

                E[i][j] = v2 + v 

            else: 

                E[i][j] = v3 + v 

  

    return E[-1][-1] 

  

  

def approximate_medoid_index_numba(series): 

    # print("len(series)", len(series)) 

    if len(series)<=50: 

        indices = range(0, len(series)) 

    else: 

        # indices = range(0, len(series)) 

        indices = np.random.choice(range(0, len(series)), 50, replace=False) 

  

    medoid_ind = -1 

    best_ss = 1e20 

    for index_candidate in indices: 

        candidate = series[index_candidate] 

        ss = sum_of_squares_ndim_numba(candidate, series) 

        # print("ss", ss) 

        if(medoid_ind==-1 or ss<best_ss): 

            best_ss = ss 

            medoid_ind = index_candidate 

    return medoid_ind 

  

  

def sum_of_squares_ndim_numba(s, series): 

    return sum(np.square(dtw_distance_ndim_set(series, s[np.newaxis, ...]))) 

  

  

@jit(nopython=True) 

def fill_delta_mat_dtw(center, s, delta_mat): 

    slim = delta_mat[:len(center), :len(s)] 

    # slim = np.subtract.outer(center, s) 

    slim = subtract_outer(center, s) 

    slim = np.square(slim) 

  

  

@jit(nopython=True) 

def mat_update_cus(center_length, s_len, cost_mat, path_mat, delta_mat): 

    for i in prange(1, center_length): 

        cost_mat[i, 0] = cost_mat[i-1, 0] + delta_mat[i, 0] 

        path_mat[i, 0] = 2 

  

    for j in prange(1, s_len): 

        cost_mat[0, j] = cost_mat[0, j-1] + delta_mat[0, j] 

        path_mat[0, j] = 1 

  

    for i in prange(1, center_length): 

        for j in prange(1, s_len): 

            diag,left,top = cost_mat[i-1, j-1], cost_mat[i, j-1], cost_mat[i-1, j] 

            if(diag <= left): 

                if(diag <= top): 

                    res = diag 

                    path_mat[i,j] = 0 

                else: 

                    res = top 

                    path_mat[i,j] = 2 

            else: 

                if(left<=top): 

                    res = left 

                    path_mat[i,j] = 1 

                else: 

                    res = top 

                    path_mat[i,j] = 2 

  

            cost_mat[i, j] = res + delta_mat[i, j] 

  

    return cost_mat, path_mat, delta_mat 

  

  

@jit(nopython=True, cache=True, fastmath=True, nogil=True) 

def DBA_update_cus(center, series, max_length): 

    cost_mat = np.empty((max_length, max_length)) 

    delta_mat = np.empty((max_length, max_length)) 

    path_mat = np.empty((max_length, max_length), dtype=np.int8) 

  

    options_argmin = [(-1, -1), (0, -1), (-1, 0)] 

    updated_center = np.zeros(center.shape) 

    n_elements = np.zeros(center.shape)  # n_elements = np.array(np.zeros(center.shape), dtype=int) 

    center_length = len(center) 

  

    for s_ind in prange(len(series)): 

        s = series[s_ind] 

        s_len = len(s) 

        # ========= REWRITE FOR SPEED, func: fill_delta_mat_dtw(center, s, delta_mat) ========= 

        c = np.empty((s.shape[1], s_len, s_len))  # c = [] 

        for n in range(center.shape[1]): 

            a_n = center[:, n] 

            b_n = s[:, n] 

            c_n = subtract_outer(a_n, b_n)  # c_n = np.subtract.outer(a_n, b_n) 

            c_n = np.square(c_n) 

            c[n] = c_n  # c.append(c_n) 

        delta_mat = np.sum(c, axis=0)  # delta_mat = np.sum(np.array(c), axis=0)         

        # ================================= REWRITE FOR SPEED ================================= 

        cost_mat[0, 0] = delta_mat[0, 0] 

        path_mat[0, 0] = -1 

        i = center_length-1 

        j = s_len-1 

        _, path_mat, _ = mat_update_cus(center_length, s_len, cost_mat, path_mat, delta_mat) 

  

        while(path_mat[i, j] != -1): 

            updated_center[i] += s[j] 

            n_elements[i] += 1 

            move = options_argmin[path_mat[i, j]] 

            i += move[0] 

            j += move[1] 

        updated_center[i] += s[j] 

        n_elements[i] += 1 

  

    return np.divide(updated_center, n_elements) 

  

  

def performDBA(series, n_iterations=10): 

    """ 

    arg: 

        series: 3d array 

                shape - (# instances, length of instance, n_dim of instance)  

    return: 

        shape 

    """ 

    max_length = reduce(max, map(len, series)) 

    # print("max_length", max_length) 

    # start0 = timeit.default_timer() 

    medoid_ind = approximate_medoid_index_numba(series) 

    # print('approximate_medoid_index time: ', timeit.default_timer() - start0) 

    center = series[medoid_ind] 

    # print("center.shape", center.shape) 

    # print("series.shape", series.shape) 

    # start = timeit.default_timer() 

    for i in range(0, n_iterations): 

        center = DBA_update_cus(center, series, max_length) 

    # print('DBA_update time: ', timeit.default_timer() - start) 

    return center 

  

  

def main(): 

    #generating synthetic data 

    n_series = 200 

    length = 50 

    print("n_series:", n_series) 

    print("length:", length) 

  

    series = list() 

    padding_length=3 

    indices = range(0, length-padding_length) 

    sin_profile_gen = np.array([np.sin(2*np.pi*j/len(indices)) for j in indices]) 

    cos_profile_gen = np.array([np.cos(2*np.pi*j/len(indices)) for j in indices]) 

    randomizer = lambda j:np.random.normal(j, 0.02) 

    randomizer_fun = np.vectorize(randomizer) 

     

    for i in range(0,n_series): 

        # series_i = randomizer_fun(sin_profile_gen) 

        series_i1 = randomizer_fun(sin_profile_gen) 

        series_i2 = randomizer_fun(cos_profile_gen) 

        series_i = np.hstack( ( series_i1.reshape((-1,1)), series_i2.reshape((-1,1)) ) ) 

        series.append(series_i) 

    series = np.array(series) 

    print(series.shape) # (n_series, length-padding_length, n_dim) 

  

    a = dtw_distance_ndim_set(series[0][np.newaxis, ...], series) 

    print(a.shape) 

  

    # print(series.shape) 

    # print(dtw_distance_ndim(series[0], series[1])) 

    # start = timeit.default_timer() 

    # for i in range(1000): 

    #     dtw_distance_ndim(series[0], series[1]) 

    # print('customized DBA time: ', timeit.default_timer() - start)  # 6s 

  

  

    # plt.plot(series[0]) 

    # plt.plot(series[1]) 

    # plt.plot(series[2]) 

    # plt.show() 

  

  

    average_series = performDBA(series[:10]) 

    start = timeit.default_timer() 

    average_series = performDBA(series) 

    print('customized DBA time: ', timeit.default_timer() - start)  # 6s 

    print(np.sum(dtw_distance_ndim_set(series, average_series[np.newaxis, ...]))) 

    print(average_series[0], average_series[-1], '\n\n') 

     

    plt.plot(average_series) 

    plt.show() 

  

  

def test_sum_square_ndim(): 

    # a1 = np.array([[0,1,2,3,2,1], [0,-1,-2,-3,-2,-1], [0,1,2,-3,-2,-1]]).T 

    # a2 = np.array([[0,1,2,3,2,1], [0,-1,-2,-3,-2,-1], [0,1,2,-3,-2,-1]]).T 

    # a3 = np.array([[0,1,2,3,2,1], [0,-1,-2,-3,-2,-1], [0,1,2,-3,-2,-1]]).T 

  

    # series = np.array([a1, a2, a3,a1, a2, a3,a1, a2, a3]) 

    # print(series.shape)  

    # # exit() 

  

    # start = timeit.default_timer() 

    # average_series = performDBA(series) 

    # print('customized DBA time: ', timeit.default_timer() - start)  # 6s 

    # print(np.sum(dtw_distance_ndim_set(series, average_series[np.newaxis, ...]))) 

    # print(average_series[0], average_series[-1], '\n\n') 

  

    # plt.plot(average_series) 

    # plt.show() 

  

    # ==================== func test_sum_square_ndim() 

    a = np.array([[1,2,3,4], [1,2,3,4], [0,1,2,3]]).T 

    b = np.array([[1,2,3,4], [10,20,30,40], [0,1,2,3]]).T 

    print(a) 

    print(b) 

    # print(np.sum(np.array([a,b]), axis=0)) 

    # print(np.sum(np.array([a,b,a]), axis=0)) 

    # exit() 

  

    c = np.empty((a.shape[1], a.shape[0], a.shape[0])) 

    for n in range(a.shape[1]): 

        a_n = a[:, n] 

        b_n = b[:, n] 

        c_n = np.subtract.outer(a_n, b_n) 

        print("subtract outer") 

        print(c_n) 

        print() 

        np.square(c_n, out=c_n) 

        print("square") 

        print(c_n) 

        print() 

        c[n] = c_n 

    print(c) 

    sum_c = np.sum(c, axis=0) 

    print(sum_c) 

  

  

def test_subtract_outer(): 

    import numba as nb 

    a_n = np.random.rand(100) 

    b_n = np.random.rand(100) 

    c_n = np.subtract.outer(a_n, b_n) 

     

    print(subtract_outer(a_n,b_n)) 

    start = timeit.default_timer() 

    for i in range(1000): 

        subtract_outer(a_n,b_n) 

    print('customized outer time: ', timeit.default_timer() - start)  # 6s 

  

  

    print(np.subtract.outer(a_n,b_n)) 

    start = timeit.default_timer() 

    for i in range(1000): 

        np.subtract.outer(a_n,b_n) 

    print('customized outer time: ', timeit.default_timer() - start)  # 6s 

  

  

def compare_dtw_ndim(): 

    """ 

    conclusion: do not use library dtwalign! wrong output 

  

    """ 

    a = np.array([[1,2,1.0,1],[1,2,1.0,3]]).T 

    b = np.array([[1,1,0.0,9],[1,1,0.0,4]]).T 

    # a = np.array([1,2,1.0]) 

    # b = np.array([1,1,0.0]) 

  

    # a_n = np.random.rand(20) 

    # b_n = np.random.rand(20) 

    # a = np.array([a_n, a_n, a_n]).T 

    # b = np.array([b_n, b_n, b_n]).T 

  

  

    from dtwalign import dtw  # cannot be used for multi-dim dtw, gives erroneous result 

    def dtw_align(vector1, vector2, dist="euclidean"):   # calculate dtw_align distance   

        # return cdtw(vector1, vector2, window_type="sakoechiba", window_size=5).distance 

        return dtw(vector1, vector2, dist).distance 

  

    dist = dtw_align(a, b) 

    print(dist) 

    # # start = timeit.default_timer() 

    # # for i in range(1000): 

    # #     dist = dtw(a, b) 

    # # print('customized DBA time: ', timeit.default_timer() - start)  # 6s 

  

  

    dist = dtw_distance_ndim(a, b) 

    print(dist) 

    # start = timeit.default_timer() 

    # for i in range(1000): 

    #     dist = dtw_distance_ndim(a, b) 

    # print('customized DBA time: ', timeit.default_timer() - start)  # 6s 

    from sklearn.metrics.pairwise import euclidean_distances 

    from dtw_np import dtw as dtw_np 

    dist_fun = euclidean_distances 

    w = np.inf 

    s = 1.0 

    dist, cost, acc, path = dtw_np(a, b, dist_fun, w=w, s=s) 

    print(dist) 

  

  

def compare_dtw_1dim(): 

    """ 

    conclusion: do not use library dtwalign! wrong output 

  

    """ 

  

    # a = np.array([1,2,1.0]) 

    # b = np.array([1,1,0.0]) 

    a = np.random.rand(20) 

    b = np.random.rand(20) 

  

    from dtwalign import dtw as cdtw  # cannot be used for multi-dim dtw, gives erroneous result 

    def dtw_align(vector1, vector2, dist="euclidean"):   # calculate dtw distance   

        # return cdtw(vector1, vector2, window_type="sakoechiba", window_size=5).distance 

        return cdtw(vector1, vector2, dist).distance 

  

    dist = dtw_align(a, b) 

    print(dist) 

    # start = timeit.default_timer() 

    # for i in range(1000): 

    #     dist = dtw(a, b) 

    # print('customized DBA time: ', timeit.default_timer() - start)  # 6s 

  

  

    dist = dtw_distance_1d(a, b) 

    print(dist) 

    start = timeit.default_timer() 

    for i in range(1000): 

        dist = dtw_distance_1d(a, b) 

    print('dtw_distance_1d time: ', timeit.default_timer() - start)  # 6s 

  

  

    from sklearn.metrics.pairwise import euclidean_distances 

    from dtw_np import dtw as dtw_np 

    dist_fun = euclidean_distances 

    w = np.inf 

    s = 1.0 

    dist, cost, acc, path = dtw_np(a, b, dist_fun, w=w, s=s) 

    print(dist) 

  

    start = timeit.default_timer() 

    for i in range(1000): 

        dist, cost, acc, path = dtw_np(a, b, dist_fun, w=w, s=s) 

    print('dtw_np time: ', timeit.default_timer() - start)  # 6s 

  

  

  

@jit(nopython=True) 

def dot1(a,b): 

    return np.dot(a,b) 

  

@jit(nopython=True) 

def dot2(a,b): 

    n = a.shape[0] 

    k = b.shape[0] 

    c = 0 

    for i in range(n): 

        for j in range(k): 

            c += a[i]*b[j] 

    return c 

  

def test_dot_prod(): 

    a = np.random.random((50)) 

    b = np.random.random((50)) 

  

    c1 = dot1(a,b) 

    start = timeit.default_timer() 

    for i in range(500): 

        c1 = dot1(a,b) 

    print('dot1: ', timeit.default_timer() - start)  # 6s 

  

    c2 = dot2(a,b) 

    start = timeit.default_timer() 

    for i in range(500): 

        c2 = dot2(a,b) 

    print('dot2: ', timeit.default_timer() - start)  # 6s 

  

  

if __name__== "__main__": 

    main() 

    # test_sum_square_ndim() 

    # test_subtract_outer() 

    # test_dot_prod() 

    # compare_dtw_ndim() 

    # compare_dtw_1dim() 

 

 