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

np.random.seed(1)

@jit(nopython=True, parallel=True, nogil=True)
def dtw_distance_set(dataset1, dataset2):
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
            dist[i][j] = dtw_distance(dataset1[i], dataset2[j])

    return dist


@jit(nopython=True, cache=True)
def dtw_distance(series1, series2):
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
    E[0][0] = v * v

    # Fill First Column
    for i in range(1, l1):
        v = series1[i] - series2[0]
        E[i][0] = E[i - 1][0] + v * v

    # Fill First Row
    for i in range(1, l2):
        v = series1[0] - series2[i]
        E[0][i] = E[0][i - 1] + v * v

    for i in range(1, l1):
        for j in range(1, l2):
            v = series1[i] - series2[j]
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


def approximate_medoid_index_numba(series):
    if len(series)<=50:
        indices = range(0,len(series))
    else:
        # indices = range(0,len(series))
        indices = np.random.choice(range(0,len(series)),50,replace=False)

    medoid_ind = -1
    best_ss = 1e20
    for index_candidate in indices:
        candidate = series[index_candidate]
        ss = sum_of_squares_numba(candidate,series)
        # print("ss", ss)
        if(medoid_ind==-1 or ss<best_ss):
            best_ss = ss
            medoid_ind = index_candidate
    return medoid_ind


def sum_of_squares_numba(s,series):
    return sum(np.square(dtw_distance_set(series, s.reshape((1,-1)))))


def fill_delta_mat_dtw(center, s, delta_mat):
    slim = delta_mat[:len(center),:len(s)]
    np.subtract.outer(center, s,out=slim)
    np.square(slim, out=slim)


@jit(nopython=True)
def mat_update_cus(center_length, s_len, cost_mat, path_mat, delta_mat):
    for i in prange(1, center_length):
        cost_mat[i, 0] = cost_mat[i-1, 0]+delta_mat[i, 0]
        path_mat[i, 0] = 2

    for j in prange(1, s_len):
        cost_mat[0, j] = cost_mat[0, j-1]+delta_mat[0, j]
        path_mat[0, j] = 1

    for i in prange(1, center_length):
        for j in prange(1, s_len):
            diag,left,top =cost_mat[i-1, j-1], cost_mat[i, j-1], cost_mat[i-1, j]
            if(diag <=left):
                if(diag<=top):
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

            cost_mat[i, j] = res+delta_mat[i, j]

    return cost_mat, path_mat, delta_mat


def DBA_update_cus(center, series, max_length):

    cost_mat = np.empty((max_length, max_length))
    delta_mat = np.empty((max_length, max_length))
    path_mat = np.empty((max_length, max_length), dtype=np.int8)

    options_argmin = [(-1, -1), (0, -1), (-1, 0)]
    updated_center = np.zeros(center.shape)
    n_elements = np.array(np.zeros(center.shape), dtype=int)
    center_length = len(center)
    for s_ind in prange(len(series)):
        s = series[s_ind]
        s_len = len(s)

        # ========= REWRITE THIS FOR FURTHER SPEEDUP
        # fill_delta_mat_dtw(center, s, delta_mat)
        slim = delta_mat[:len(center),:len(s)]
        np.subtract.outer(center, s,out=slim)
        np.square(slim, out=slim)
        # ========= REWRITE THIS FOR FURTHER SPEEDUP

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
    max_length = reduce(max, map(len, series))
    # start0 = timeit.default_timer()
    medoid_ind = approximate_medoid_index_numba(series)
    # print('approximate_medoid_index time: ', timeit.default_timer() - start0)
    center = series[medoid_ind]
    # start = timeit.default_timer()
    for i in range(0, n_iterations):
        center = DBA_update_cus(center, series, max_length)
    # print('DBA_update time: ', timeit.default_timer() - start)
    return center


def main():
    #generating synthetic data
    n_series = 50
    length = 200
    print("n_series:", n_series)
    print("length:", length)

    series = list()
    padding_length=30
    indices = range(0, length-padding_length)
    main_profile_gen = np.array([np.sin(2*np.pi*j/len(indices)) for j in indices])
    randomizer = lambda j:np.random.normal(j,0.02)
    randomizer_fun = np.vectorize(randomizer)
    
    for i in range(0,n_series):
        series_i = randomizer_fun(main_profile_gen)
        series.append(series_i)
    series = np.array(series)

    print(series.shape)
    plt.plot(series[0])
    plt.plot(series[1])
    plt.plot(series[2])
    plt.show()

    start = timeit.default_timer()
    average_series = performDBA(series)
    print('customized DBA time: ', timeit.default_timer() - start)  # 6s
    print(np.sum(dtw_distance_set(series,average_series.reshape((1,-1)))))
    print(average_series[0], average_series[-1], '\n\n')
    
    plt.plot(average_series)
    plt.show()


if __name__== "__main__":
    main()