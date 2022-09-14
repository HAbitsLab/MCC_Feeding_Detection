import pandas as pd
import numpy as np
import pickle as pkl
import scipy
from copy import deepcopy
import seaborn as sns
import warnings
import timeit
import random
import pickle
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split
from tslearn.preprocessing import TimeSeriesScalerMeanVariance, TimeSeriesResampler
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, AdaBoostClassifier
from util import get_test_x, get_0, clf_train, clf_pred, get_pred_0, train_mcc, pred_instance, get_result
from overlap import overlap_len, overlap_perc, combine_overlap, overlap_seg, combine_continous, mergeIntervals
from evaluation import FPR, FNR, feeding_sensitivity, hit_rate, window_based_evl, gesture_based_evl
from process import extract_train_by_participant, subsample_by_participant
from sklearn import preprocessing
from scipy.stats import *
from numpy import *
import sys
sys.path.append('../mcc_v2')
from mcc import MCClassifier
from cdtw import dtw
from dtw_ndim_modified import dtw_ndim
warnings.filterwarnings("ignore")
random.seed(0)
np.random.seed(0)

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

def get_train_for_subject(p, x_train_sub_all, y_train_sub_all):
    '''
    Get train and test for specific subject (LOSO).
    
    :param int p: participant number 1-12.
    :param list x_train_sub_all, y_train_sub_all: train x and y from all participants.
    
    :return list x_train, y_train: train x and y for specific participant.
    '''
    p = p - 1
    x_train = x_train_sub_all[:p] + x_train_sub_all[p+1:]
    y_train = y_train_sub_all[:p] + y_train_sub_all[p+1:]
    return(x_train, y_train)


# Example: in-lab FIC
PATH = '../Data/FIC/ml_data/train_mean_LOSO.pkl' 
with open(PATH) as f:
    x_mean = pkl.load(f)
    
subject = list(set(x_mean['subject']))
print('Participant ID:', subject)
print('Meal session:', x_mean['subject'])

# Select Model
models = ['mcc','rdf','knn','svm','cnn_lstm','resnet_cnnlstm','nb','thresholding']
model = models[0]
modes = ['personalized', 'all']
goal = 0.80

# personalized model 
if((model == 'mcc') and (mode == 'personalized')):
    centers_all = []
    thres_all = []
    x_train_sub_all, y_train_sub_all = extract_train_by_participant(x_mean)
    for j in range(len(x_train_sub_all)):
        # setting: accelerometer x/y/z only
        centers, thres = train_mcc(x_train_sub_all[j][:,:,:3], y_train_sub_all[j], 0.90)
        centers_all.append(centers)
        thres_all.append(thres)

    best_f1_win = 0
    best_f1_ges = 0

    while(best_f1_win < goal or best_f1_ges < goal):

        session_list = []
        participant_list = []

        # window-based
        precision_list_win = []
        recall_list_win = []
        f1_list_win = []
        acc_list_win = []

        # gesture-based
        precision_list = []
        recall_list = []
        f1_list = []
        acc_list = []

        x_train_all_p, y_train_all_p = extract_train_by_participant(x_mean)

        for p in subject:
            print('Participant:', p)
            train_example, train_y_example = get_train_for_subject(p, x_train_all_p, y_train_all_p)
            x_train = np.vstack(train_example)[:,:,:6]
            y_train = np.array([item for sublist in train_y_example for item in sublist])
            
            # training
            #from inert_kyritsis_model import Model
            clf = Model(189)
            clf.fit(x_train,y_train)
            
            # get test
            sessions = [i for i,x in enumerate(x_mean['subject']) if x == p]
            for each_session in sessions:
                test_time_total = 0
                participant_list.append(p)
                session_list.append(each_session)

                test_1 = x_mean['x_test_all'][each_session]
                label_1 = x_mean['y_test_all'][each_session]
                # get negative label
                label_0 = get_0(label_1, test_1)

                pred_list = []
                for overlap in [0.5, 1]:
                    x_test, x_test_timestamp = get_test_x(test_1, overlap)
                    x_test = x_test[:,:,:6]
                    
                    # change for getting 1-rdf, 2-knn and 3-svm model
                    pred = clf.predict(x_test)
                    
                    pred_1 = x_test_timestamp[np.where(pred >= 0.5)[0]]
                    pred_0 = x_test_timestamp[np.where(pred < 0.5)[0]]

                    pred_list.append(pred_1)

                # merge continous predicted segments
                pred_1st = combine_continous(pred_list[0])
                pred_2nd = combine_continous(pred_list[1])

                # union prediction results from overlapping windows
                pred_1 = np.array(mergeIntervals(combine_overlap(pred_1st, pred_2nd).tolist()))
                pred_0 = get_pred_0(pred_1, test_1)

                label_1 = np.array(label_1[['start','end']])

                # window-based evaluation
                Precision_win, Recall_win, F1_win, Accuracy_win = window_based_evl(pred_1, pred_0, label_1, label_0)
                precision_list_win.append(Precision_win)
                recall_list_win.append(Recall_win)
                f1_list_win.append(F1_win)
                acc_list_win.append(Accuracy_win)

                # gesture-based evaluation
                Precision, Recall, F1, Accuracy = gesture_based_evl(label_1, pred_1, label_0, pred_0)
                precision_list.append(Precision)
                recall_list.append(Recall)
                f1_list.append(F1)
                acc_list.append(Accuracy)

        if(best_f1_win < np.mean(f1_list_win)):
            best_f1_win = np.mean(f1_list_win)
        if(best_f1_ges < np.mean(f1_list)):
            best_f1_ges = np.mean(f1_list)

if((model == 'mcc') and (mode == 'all')):
    best_f1_win = 0
    best_f1_ges = 0

    while(best_f1_win < goal or best_f1_ges < goal):
        session_list = []
        participant_list = []

        # window-based
        precision_list_win = []
        recall_list_win = []
        f1_list_win = []
        acc_list_win = []

        # gesture-based
        precision_list = []
        recall_list = []
        f1_list = []
        acc_list = []

        centers_all = centers_all_list
        thres_all = thres_all_list

        for p in subject:
            print('Participant:', p)
            centers_final, thres_final = get_result(p, centers_all, thres_all)

            # get test
            sessions = [i for i,x in enumerate(x_mean['subject']) if x == p]
            for each_session in sessions:
                test_time_total = 0
                participant_list.append(p)
                session_list.append(each_session)

                test_1 = x_mean['x_test_all'][each_session]
                label_1 = x_mean['y_test_all'][each_session]
                # get negative label
                label_0 = get_0(label_1, test_1)

                pred_list = []
                for overlap in [0.5, 1]:
                    x_test, x_test_timestamp = get_test_x(test_1, overlap)
                    x_test = x_test[:,:,:3]

                    pred = []
                    for i in x_test:
                        pred.append(pred_instance(i, centers_final, thres_final))
                    pred = np.array(pred)
                    pred_1 = x_test_timestamp[np.where(pred == 1)]
                    pred_0 = x_test_timestamp[np.where(pred == 0)]

                    pred_list.append(pred_1)

                # merge continous predicted segments
                pred_1st = combine_continous(pred_list[0])
                pred_2nd = combine_continous(pred_list[1])

                # union prediction results from overlapping windows
                pred_1 = np.array(mergeIntervals(combine_overlap(pred_1st, pred_2nd).tolist()))
                pred_0 = get_pred_0(pred_1, test_1)

                label_1 = np.array(label_1[['start','end']])

                # window-based evaluation
                Precision_win, Recall_win, F1_win, Accuracy_win = window_based_evl(pred_1, pred_0, label_1, label_0)
                precision_list_win.append(Precision_win)
                recall_list_win.append(Recall_win)
                f1_list_win.append(F1_win)
                acc_list_win.append(Accuracy_win)

                # gesture-based evaluation
                Precision, Recall, F1, Accuracy = gesture_based_evl(label_1, pred_1, label_0, pred_0)
                precision_list.append(Precision)
                recall_list.append(Recall)
                f1_list.append(F1)
                acc_list.append(Accuracy)

        if(best_f1_win < np.mean(f1_list_win)):
            best_f1_win = np.mean(f1_list_win)
        if(best_f1_ges < np.mean(f1_list)):
            best_f1_ges = np.mean(f1_list)


## Model Optimization
def get_train_for_subject_flat(p):
    '''
    Get train and test for specific subject (combined.)
    
    :param int p: participant number 1-12.
    
    :return list x_train, y_train: train x and y for specific participant (combined).
    '''
    p = p - 1
    x_train = x_train_sub_all[:p] + x_train_sub_all[p+1:]
    y_train = y_train_sub_all[:p] + y_train_sub_all[p+1:]
    x_train_final = (np.vstack(x_train))
    y_train_final = flat_list = [item for sublist in y_train for item in sublist]
    return(x_train_final, y_train_final)

def pred_instance_single(data, center, thres):
    '''
    Prediction of MCC - individual function.
    
    :param ndarray data: test sample signal.
    :param ndarray center: selected centroid.
    :param float thres: corresponding tresholds.
    
    :return result: 1(positive) or 0(negative) for predition.
    '''
    if dtw(data, center) <= thres:
        return(1)
    else:
        return(0)

train_example, train_y_example = get_train_for_subject(p)
train_y_example = np.array(train_y_example)
centers, thres = get_result(p, centers_all, thres_all)

# get the predition results for all centers and thresholds
sub_list_freeze = {}
penalty_list_freeze = {}

keys = range(len(centers))
for i in keys:
    pred = []
    for each_x in train_example[:,:,:3]:
        pred.append(pred_instance_single(each_x, centers[i], thres[i]))
    pred = np.array(pred)
    
    true_pos = np.where((pred == 1)&(train_y_example==1))[0]
    false_pos = np.where((pred == 1)&(train_y_example==0))[0]
    
    sub_list_freeze[i] = true_pos
    penalty_list_freeze[i] = false_pos

full_list = np.where(train_y_example == 1)[0]
sub_list = copy.deepcopy(sub_list_freeze)
penalty_list = copy.deepcopy(penalty_list_freeze)

def select_top_N(full_list, sub_list, penalty_list, top_n = 10, ratio = 0.1):

    top_list = []
    top_key = []
    top_incorrect = []
    incorrect_all = []
    cur_n = 0

    len_all = len(full_list)

    while(cur_n < top_n):
        # get the most overlapped key of the sub_lists with remaining full_list

        #print(len(sub_list))
        best_key = max(sub_list, key = lambda x: len(set.intersection(set(full_list), set(sub_list[x]))))
        # get the sublists
        best_list = sub_list.pop(best_key)

        # get new incorrect cases
        new_incorrect = len(penalty_list[best_key]) - len(set.intersection(set(incorrect_all), set(penalty_list[best_key])))

        # get new correct cases
        new_correct = len(set.intersection(set(full_list), set(best_list)))

        if(new_correct == 0):
            print('Zero new correct cases found')
            return(top_key)

        if(new_incorrect/new_correct > ratio):
            continue
        else:
            print('New correct cases:', new_correct)
            print('New incorrect cases:', new_incorrect)
            print('Penalty Ratio:', new_incorrect/new_correct)

            # save the results
            top_key.append(best_key)
            top_list.append(best_list)
            # save incorrect cases
            top_incorrect.append(penalty_list[best_key])
            # update full list by removing the best selected sublists
            full_list = [i for i in full_list if i not in best_list]
            # update all unique incorrect cases 
            incorrect_all = set([item for sublist in top_incorrect for item in sublist])

            cur_n = cur_n + 1

            print('Current coverage:', len(set([item for sublist in top_list for item in sublist])) / len_all)
            print('--------------------------')
    
    return(top_key)