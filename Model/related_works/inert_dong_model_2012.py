import numpy as np
from sklearn.naive_bayes import GaussianNB
from scipy.stats import *
from numpy import *
import itertools
from itertools import permutations
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

    def optimize(self, x_validate, y_validate, goal=0.80, iteration = 10000, best=True):
        # optimize the parameters by grid-search
        cur_iteration = 0
        max_accuracy = 0

        # candidate parameters
        T1_list = list(range(-20,20,1))
        T2_list = list(range(-20,20,1))
        T3_list = list(range(-20,20,1))
        T4_list = list(range(-20,20,1))

        unique_combinations = []
        unique_combinations_2 = []
        permut = itertools.permutations(T1_list, len(T2_list))
        permut_2 = itertools.permutations(T3_list, len(T4_list))
        for comb in permut:
            zipped = zip(comb, T1_list)
            unique_combinations.append(list(zipped))
        for comb in permut2:
            zipped = zip(comb, T3_list)
            unique_combinations_2.append(list(zipped))

        # candicate T1, T2, T3, T4
        T1_temp  = 0; T2_temp  = 0; T3_temp  = 0; T4_temp = 0

        for i in range(len(unique_combinations)):
            cur_T1 = unique_combinations[0]
            cur_T2 = unique_combinations[1]
            cur_T3 = unique_combinations[2]
            cur_T4 = unique_combinations[3]
            y_pred = self.predict(x_y_validate)
            cur_accuracy = sum(y_pred == y_validate) / len(y_validate)
            if(cur_iteration = iteration or cur_accuracy >= goal):
                self.T1 = cur_T1 
                self.T2 = cur_T2 
                self.T3 = cur_T3 
                self.T4 = cur_T4 
                break
            elif(cur_accuracy > max_accuracy):
                max_accuracy = cur_accuracy
                T1_temp = cur_T1 
                T2_temp = cur_T2 
                T3_temp = cur_T3 
                T4_temp = cur_T4 

        # return best if running out of options
        if(best):
            self.T1 = T1_temp 
            self.T2 = T2_temp 
            self.T3 = T3_temp 
            self.T4 = T4_temp




