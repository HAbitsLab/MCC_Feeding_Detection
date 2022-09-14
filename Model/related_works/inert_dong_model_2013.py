import numpy as np
from sklearn.naive_bayes import GaussianNB
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