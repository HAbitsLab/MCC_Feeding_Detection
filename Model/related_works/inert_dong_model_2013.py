import numpy as np
from sklearn.naive_bayes import GaussianNB
from scipy.ndimage import gaussian_filter
from scipy.stats import *
from numpy import *
import joblib

'''
Dong et al approach (2013):
Predict feeding gesture based on 4 motion-based features: manipulation((deg/sec)/G), acceleration(G), roll motion(deg/sec), and roll regularity(%time) from accelerometer and gyroscope data.
Link: https://ieeexplore.ieee.org/document/6601618

Model parameters:
GaussianNB()
'''

class Model():
    def __init__(self):
        self.clf_nb = None

    def extract_motion_features(self, x_train):
        x_train_features = []
        signal_length = x_train.shape[1]
        for i in range(x_train.shape[0]):
            feature_1 = np.sum((np.abs(x_train[i][:,3]) + np.abs(x_train[i][:,4]) + np.abs(x_train[i][:,5]))/(np.abs(x_train[i][:,0]) + np.abs(x_train[i][:,1]) + np.abs(x_train[i][:,2])))/signal_length
            feature_2 = np.sum(np.abs(x_train[i][:,0]) + np.abs(x_train[i][:,1]) + np.abs(x_train[i][:,2]))/signal_length
            feature_3 = np.mean(np.abs(np.abs(x_train[i][:,5]) - np.mean(np.abs(x_train[i][:,5]))))
            feature_4 = sum(np.abs(x_train[i][:,5])>10)/signal_length
            x_train_features.append([feature_1, feature_2, feature_3, feature_4])
        x_train_features = np.array(x_train_features)
        return(x_train_features)

    def fit(self, features, targets):
        features = self.extract_motion_features(features)
        clf_nb = GaussianNB()
        clf_nb.fit(features, targets)
        self.clf_nb = clf_nb

    def predict(self, features):
    	features = self.extract_motion_features(features)
    	pred_nb = self.clf_nb.predict(features)
    	return(pred_nb)

    def save(self, dir_save):
    	joblib.dump(self.clf_nb, dir_save + 'nb.sav')


def preprocessing(data, data_type='FIC'):
    '''
    Dong et al approach (2013) required preprocessing:
    Input data: input data chosen from three datasets:  FIC, OREBA, and Clemson.
    Required steps:
        1) Gaussian-weighted smoothing for window size = 1 min (page 4)
    '''
    if(data_type == 'FIC'):
        FREQ = 100
        # LOSO train/test split, output from inlab_fic_preprocessing.py 
        train_x, train_y = data['x_train_all'], data['y_train_all']
        test_x, test_y = data['x_test_all'], data['y_test_all'] # testing by session
    elif(data_type == 'OREBA'):
        FREQ = 64
        # Random split, 61, 20 amd 19 sessions train/validation/test
        all_p = data.keys()
        random.shuffle(all_p) # random shuffle the sessions
        train_x = []
        train_y = []
        valid_x = []
        valid_y = []
        test_x = []
        test_y = []
        for i in range(61):
            train_x.append(data[all_p[i]]['x_train'])
            train_y.append(data[all_p[i]]['y_train'])
        for j in range(61, 61+20):
            valid_x.append(data[all_p[j]]['x_train'])
            valid_y.append(data[all_p[j]]['y_train'])
        for k in range(61+20, 61+20+19):
            test_x.append(data[all_p[k]]['x_train'])
            test_y.append(data[all_p[k]]['y_train'])
    elif(data_type == 'Clemson'):
        FREQ = 15
        # Random split, 302, 92 amd 93 sessions train/validation/test
        all_p = data.keys()
        random.shuffle(all_p) # random shuffle the sessions
        train_x = []
        train_y = []
        valid_x = []
        valid_y = []
        test_x = []
        test_y = []
        for i in range(302):
            train_x.append(data[all_p[i]]['x_train'])
            train_y.append(data[all_p[i]]['y_train'])
        for j in range(302, 302+92):
            valid_x.append(data[all_p[j]]['x_train'])
            valid_y.append(data[all_p[j]]['y_train'])
        for k in range(302+92, 302+92+93):
            test_x.append(data[all_p[k]]['x_train'])
            test_y.append(data[all_p[k]]['y_train'])
    else:
        print('Dataset not defined, please select from FIC, OREBA, and Clemson.')
        break

    # define the window size
    # page 4: 1 min window for smoothing over brief vigorous motions
    LENGTH = 60 * FREQ 

    train_x_final = []
    valid_x_final = []
    test_x_final = []

    if(data_type == 'FIC'):
        for i in range(train_x.shape[0]/LENGTH):
            train_x_final.append(gaussian_filter(train_x[i, i + LENGTH], sigma=10))
        for j in range(test_x.shape[0]/LENGTH):
            test_x_final.append(gaussian_filter(test_x[j, j + LENGTH], sigma=10))
        return(x_train_final, train_y, x_test_final, test_y)
    else:
        for i in range(train_x.shape[0]/LENGTH):
            train_x_final.append(gaussian_filter(train_x[i, i + LENGTH], sigma=10))
        for j in range(valid_x.shape[0]/LENGTH):
            valid_x_final.append(gaussian_filter(valid_x[j, j + LENGTH], sigma=10))
        for k in range(test_x.shape[0]/LENGTH):
            test_x_final.append(gaussian_filter(test_x[k, k + LENGTH], sigma=10))
        return(x_train_final, train_y, x_valid_final, valid_y, x_test_final, test_y)

