import numpy as np
from numpy import *
from scipy.stats import *
import timeit
from sklearn import preprocessing
import sys
sys.path.append('../mcc_v3')
from mcc import MCClassifier
from cdtw import dtw
from dtw_ndim_modified import dtw_ndim


def get_0(label_1, test_1):
    '''
    Get all negative class labels from positive labels and original data.
    
    :param dataframe label_1: pandas dataframe of all start and end time for positive labels (shape: Nx2).
    :param dataframe test_1: pandas dataframe of all start and end time of the data (shape: NxM).

    :return ndarray result: numpay array of all start and end time for negative labels (shape: Nx2).
    '''
    start_temp = list(label_1['end'])
    end_temp = list(label_1['start'])
    if(test_1['time'][0] < end_temp[0]):
        start_temp.insert(0, test_1['time'][0])
    else:
        del end_temp[0]
    end_temp.append(test_1['time'][test_1.shape[0]-1])

    # remove invalid start and end time (end < start)
    result_temp = np.column_stack([start_temp, end_temp])
    result = result_temp[np.where(result_temp[:,1] > result_temp[:,0])]

    return (result)


def get_test_x(test_1, overlap = 1):
    '''
    Get the window-sliced X_test and X_test_timestamp from X_test stream.
    
    :param dataframe test_1: pandas dataframe of test samples.
    :param float overlap: overlap percentage between adjacent windows (0,1]
    
    :return ndarray x_test: X for testing (shape: Nx6)
    :return ndarray x_test_timestamp: start and end time for each x_test sample (shape:Nx2) 
    '''
    
    # set sliding window size for testing
    win_size = 189
    x_test = []
    x_test_timestamp = []
    
    # segment stream into windows and iterate through
    for i in range(int(win_size * (1-overlap)), test_1.shape[0]-win_size-1, win_size-1):
        x_window = test_1.loc[i:i+win_size-1]
        x_window = x_window.reset_index(drop=True)
        x_test.append(np.array(x_window)[:,1:7]) #add x_test
        x_test_timestamp.append([x_window['time'][0], x_window['time'][x_window.shape[0]-1]]) #add each window's start and end timestamp
    x_test = np.array(x_test)
    x_test_timestamp = np.array(x_test_timestamp)

    return(x_test, x_test_timestamp)


def clf_train(x_train, y_train, clf, target_precision, clf_type = 'others'):
    '''
    Train classifier on training set and record run time.
    
    :param ndarray x_train: training sample x
    :param array/list y_train: training label y
    :param string clf_type: type of classifier, special case for 'mcc'
    :param object clf: initialized classifier
    
    :return object clf: trained classifier
    :return float t_train: total time for training
    '''
    if(clf_type == 'mcc'):
        x_train_list = []
        for each in x_train:
            x_train_list.append(each)

        y_train_list = y_train
        
        start = timeit.default_timer()
        centers, thres, history_best_precision = clf.train(x_train_list, y_train_list, stop_criterion=target_precision)
        t_train = timeit.default_timer() - start
    else:
        start = timeit.default_timer()
        clf.fit(x_train, y_train)
        t_train = timeit.default_timer() - start
    return(clf, t_train)

def clf_pred(x_test, x_test_timestamp, clf_trained, clf_type='others'):
    '''
    Run prediction on testing set by sliding window with overlapping percentage.
    
    :param dataframe x_test: pandas dataframe of test samples.
    :param dataframe x_test_timestamp: pandas dataframe of test timestamp
    :param object clf: pre-trained classifier
    :param string clf_type: type of classifier, special case for 'mcc'
    
    :return ndarray pred_1: positive prediction results (start and end time)
    :return ndarray pred_0: negative prediction results (start and end time)
    :return float t_test: total time for testing
    '''
         
    #train the selected classifier
    if(clf_type == 'mcc'):
        print('Predicting')
        start = timeit.default_timer()
        pred = []
        for each in x_test:
            pred.append(clf_trained.pred_instance(each))
        t_test = timeit.default_timer() - start
    else:
        print('Predicting')
        start = timeit.default_timer()
        pred = clf_trained.predict(x_test)
        t_test = timeit.default_timer() - start
    
    pred = np.array(pred)
    pred_1 = x_test_timestamp[np.where(pred == 1)]
    pred_0 = x_test_timestamp[np.where(pred == 0)]
    return (pred, pred_1, pred_0, t_test)

def get_pred_0(pred_1, test_1):
    # get predition timestamp of non-feeding
    if(len(pred_1) == 0):
        return(np.array([[test_1['time'][0], test_1['time'][test_1.shape[0]-1]]]))

    start_temp = list(pred_1[:,1])
    end_temp = list(pred_1[:,0])
    if(test_1['time'][0] < end_temp[0]):
        start_temp.insert(0, test_1['time'][0])
    else:
        del end_temp[0]
    end_temp.append(test_1['time'][test_1.shape[0]-1])

    # remove invalid start and end time (end < start)
    result_temp = np.column_stack([start_temp, end_temp])
    result = result_temp[np.where(result_temp[:,1] > result_temp[:,0])]

    return(result)

def train_mcc(x_train, y_train, target_precision):
    '''
    Train MCC-classifier from train and labels. Stopping criteria: reach target_precision or 30 templates.
    
    :param array x_train: numpy array for training signal (default shape: 189xNx3).
    :param array y_train: numpy array for training labels (feeding vs non-feeding) (default shape: Nx1).
    :param float target_precision: target precision treshold.

    :return list centers, thres: trained template and thresholds when reaching the target_precision.
    '''
    clf = MCClassifier(metric="dtw", seed_mode="costest")
    x_train_list = []
    for each in x_train:
        x_train_list.append(each)
    y_train_list = y_train
    centers, thres, history_best_precision = clf.train(x_train_list, y_train_list, stop_criterion=target_precision)
    return(centers, thres)

def pred_instance(data, centers, thres):
    '''
    Customized function for MCC-classifier prediction.
    
    :param array data: numpy array for prediction (default shape: 189xNx3).
    :param list centers: trained templates from train_mcc.
    :param list thres: trained tresholds from train_mcc.

    :return array pred: prediction list literating over all centers and thresholds.
    '''
    pred = 0
    upper = 1
    for center, thre in zip(centers, thres):
        if dtw(data, center) <= thre*upper:
            pred = 1
            break
    return pred

def get_result(p, centers_all, thres_all):
    '''
    Customized function for MCC-classifier prediction.
    
    :param int p: participant number.
    :param list centers_all: trained templates from train_mcc.
    :param list thres_all: trained tresholds from train_mcc.

    :return list centers, thresholds: centers and thresholds for the given participant.
    '''
    p = p - 1
    return(centers_all[p], thres_all[p])