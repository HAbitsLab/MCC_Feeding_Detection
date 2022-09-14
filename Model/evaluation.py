import numpy as np
from overlap import overlap_len
from overlap import overlap_perc

def FPR(pred_1, label_0):
    '''
    Calculate False Alarm Rate (false positive) based on true label and prediction.
    
    :param ndarray pred_combined: start and end time of positive prediction (shape: Nx2).
    :param dataframe label_0: pandas dataframe of all start and end time for negative labels (shape: Nx2).
    :return float: false alarm rate.
    '''
    L_pred_1_true_0 = overlap_len(pred_1, label_0)
    L_true_0 = (np.sum(np.array(label_0)[:,0:2], axis=0)[1] - np.sum(np.array(label_0)[:,0:2], axis=0)[0])
    return (L_pred_1_true_0/L_true_0)

def FNR(pred_0, label_1):
    '''
    Calculate Missed Detection Rate (false negative) based on true label and prediction.
    
    :param ndarray pred_0: start and end time of nagative prediction (shape: Nx2).
    :param dataframe label_1: pandas dataframe of all start and end time for positive labels (shape: Nx2).
    :return float: missed detection rate.
    '''
    L_pred_0_true_1 = overlap_len(pred_0, np.array(label_1)[:,0:2])
    L_true_1 = (np.sum(np.array(label_1)[:,0:2], axis=0)[1] - np.sum(np.array(label_1)[:,0:2], axis=0)[0])
    return (L_pred_0_true_1/L_true_1)

def feeding_sensitivity(pred_1, label_1):
    '''
    Calculate Gesture sensitivity rate based on true label and prediction.
    
    :param ndarray pred_1: start and end time of positive prediction (shape: Nx2).
    :param dataframe label_1: pandas dataframe of all start and end time for positive labels (shape: Nx2).
    :return float: sensitivity rate.
    '''
    L_pred_1_true_1 = overlap_len(pred_1, np.array(label_1)[:,0:2])
    L_true_1 = (np.sum(np.array(label_1)[:,0:2], axis=0)[1] - np.sum(np.array(label_1)[:,0:2], axis=0)[0])
    return (L_pred_1_true_1/L_true_1)

def hit_rate(pred_1, label_1):
    '''
    Calculate Hit Rate based on true label and prediction.
    Hit rate is defined as number of correct possitive prediction by number of total positive segments.
    
    :param ndarray pred_1: start and end time of positive prediction (shape: Nx2).
    :param dataframe label_1: pandas dataframe of all start and end time for positive labels (shape: Nx2).
    :return float: hit rate.
    '''
    hit = 0
    for i in range(pred_1.shape[0]):
        a_s = pred_1[i][0]
        a_e = pred_1[i][1]

        for j in range(label_1.shape[0]):
            b_s = label_1['start'][j]
            b_e = label_1['end'][j]

            if ((a_s < b_e) & (b_s < a_e)): # overlap
                total = max(a_s,a_e,b_s,b_e) - min(a_s,a_e,b_s,b_e)
                overlap = (a_e - a_s) + (b_e - b_s) - total
                overlap_perc = overlap / (b_e - b_s) 
                if(overlap_perc > 0.5):
                    hit = hit + 1
    return (hit / label_1.shape[0])
    
def window_based_evl(pred_1, pred_0, label_1, label_0, weight=1.0):
    '''
    Run window-based evaluation metrics on prediction results. 
    All four metrics are measured by the overlap in time duration between predicted window and ground truth.
    
    :param ndarray pred_1: positive prediction results (start and end time)
    :param ndarray pred_0: negative prediction results (start and end time)
    :param dataframe label_1: pandas dataframe of positive testing label y
    :param dataframe label_0: pandas dataframe of negative testing label y
    
    :return float Precision: TP / (TP + FP)
    :return float Recall: TP / (TP + FN)
    :return float F1: 2 * (Precision * Recall) / (Precision + Recall)
    :return float Accuracy(weighted): (TP * weight + TN) / ((TP+TN)*weight + FP + FN)
    '''   
    TP = overlap_len(pred_1, label_1)
    TN = overlap_len(pred_0, label_0)
    FP = overlap_len(pred_1, label_0)
    FN = overlap_len(pred_0, label_1)
    try:
        Precision = TP/(TP+FP)
    except:
        Precision = 0
    try:
        Recall = TP/(TP+FN)
    except:
        Recall = 0
    try:
        F1 = 2 * (Precision*Recall)/(Precision+Recall)
    except:
        F1 = 0
    try:
        Accuracy = (TP * weight + TN) / ((TP+TN) * weight + FP + FN)
    except:
        Accuracy = 0    
    return(Precision, Recall, F1, Accuracy) 


def gesture_based_evl(label_1, pred_1, label_0, pred_0, weight=1.0):
    '''
    Run gesture-based evaluation metrics on prediction results
    
    :param ndarray pred_1: positive prediction results (start and end time)
    :param ndarray pred_0: negative prediction results (start and end time)
    :param ndarray label_1: ndarray of positive testing label y
    :param ndarray label_0: ndarray of negative testing label y
    
    :return float Precision: TP / (TP + FP)
    :return float Recall: TP / (TP + FN)
    :return float F1: 2 * (Precision * Recall) / (Precision + Recall)
    :return float Accuracy(weighted): (TP * weight + TN) / ((TP+TN)*weight + FP + FN)
    ''' 
    TP = 0
    TN = 0
    FP = 0
    FN = 0

    for i in range(label_1.shape[0]):
        for j in range(pred_1.shape[0]):
            if (overlap_perc(label_1[i], pred_1[j:j+1]) >= 0.5):
                TP = TP + 1
                break
    FP = pred_1.shape[0] - TP

    for j in range(pred_0.shape[0]):
        for i in range(label_1.shape[0]):
            if (overlap_perc(label_1[i], pred_0[j:j+1]) >= 0.5):
                FN = FN + 1
                break
            else:
                TN = TN + 1
                break

    try:
        Precision = TP/(TP+FP)
    except:
        Precision = 0
    try:
        Recall = TP/(TP+FN)
    except:
        Recall = 0
    try:
        F1 = 2 * (Precision*Recall)/(Precision+Recall)
    except:
        F1 = 0
    try:
        Accuracy = (TP * weight + TN) / ((TP+TN) * weight + FP + FN)
    except:
        Accuracy = 0   
    return(Precision, Recall, F1, Accuracy)