import numpy as np
from sklearn.naive_bayes import GaussianNB
from scipy.stats import *
from numpy import *
import joblib

'''
Dong et al approach (2012):
A New Method for Measuring Meal Intake in Humans via Automated Wrist Motion Tracking
Predict feeding gesture based on setting treshold for detecting bites to infer intake gestures.
Link: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4487660/
'''

class Model():
    def __init__(self, freq, T1=10, T2=10, T3=2, T4=8): # default parameters from paper 
        self.freq = freq
        self.T1 = T1
        self.T2 = T2
        self.T3 = T3
        self.T4 = T4

    def predict(self, x_train):
    	pred_y = []
        T1 = self.T1; T2 = self.T2; T3 = self.T3; T4 = self.T4
        for each_segment in x_train:
            t = 0
            preds=[]
            for each_frame in each_segment: 
                s = 0
                event = 0
                # Loop through time frames
                # Roll velocity is the radial velocity of x axis in features
                v_t = each_frame[4]
                # Wrist roll velocity must surpass a positive threshold.
                if int(v_t) > T1 and event == 0:
                    event = 1
                    s = t
                # A minimum amount of time must pass and the velocity must surpass a negative threshold.
                if int(v_t) < T2 and t-s > T3 * self.freq and event == 1:
                    s = t
                    event = 2
                    preds.append(1) # bite detected
                else:
                    preds.append(0) # bite undetected
                if(event == 2 and t-s > T4 * self.freq):
                    event = 0    
                t = t + 1/self.freq   
            if(sum(preds) != 0):
                pred_y.append(1)
            else:
                pred_y.append(0)
    	return(np.array(pred_y))