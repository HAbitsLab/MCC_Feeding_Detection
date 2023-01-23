import numpy as np
from tensorflow.keras.layers import Dense, MaxPooling1D, LSTM, Flatten, Dropout, Conv1D, TimeDistributed, BatchNormalization
from tensorflow.keras.wrappers.scikit_learn import KerasClassifier
from tensorflow.keras.models import Sequential
from sklearn.model_selection import StratifiedKFold, cross_val_score
from keras.optimizers import RMSprop, Adam
from scipy.stats import *
from numpy import *
import random
import joblib

'''
Kyritsis et al approach:
Predict feeding gesture from CNN-LSTM model. Code and hyperparameters adopted from the authors, slight modification fot input shape.
Link: https://ieeexplore.ieee.org/document/9056472
'''

class Model():
    def __init__(self, input_length):
        self.input_length = input_length
        self.clf_cnnlstm = None

    def model(self):
        this_optimizer = RMSprop()
        model = Sequential()
        model.add(Conv1D(filters=32, kernel_size=5, padding='same',
                         activation='relu', input_shape=(self.input_length, 6)))
        model.add(BatchNormalization())
        model.add(MaxPooling1D())
        model.add(Conv1D(filters=64, kernel_size=3,
                         padding='same', activation='relu'))
        model.add(BatchNormalization())
        model.add(MaxPooling1D())
        model.add(Conv1D(filters=128, kernel_size=3,
                         padding='same', activation='relu'))
        model.add(BatchNormalization())
        model.add(LSTM(128, dropout=0.2, recurrent_dropout=0.5))
        model.add(Dropout(0.5))
        model.add(Dense(1, activation='sigmoid'))
        model.compile(loss='binary_crossentropy',
                      optimizer=this_optimizer, metrics=['accuracy'])
        return model

    def fit(self, features, targets):
        clf_cnnlstm = self.model()

        # page 26 - data augmentation: 50% to rotate around x and z axes
        # final randomization inlcudes: Qx, Qz, Qx * Qz, Qz * Qx
        feature_final = []
        for i in range(features.shape[0]):
            mini_batch = features[i]
            if random.random() < 0.5: # 50% change to get transformed
                # normal distribution, mean = 0, std = 10
                q_x = np.random.normal(0, 10, 1)[0] 
                q_z = np.random.normal(0, 10, 1)[0]
                flip_x = np.array([q_x, 1, 1])
                flip_z = np.array([1, 1, q_z])
                flip_x_z = np.array([q_x, 1, q_z])
                flip_z_x = np.array([q_z, 1, q_x])
                random_flip = random.choice([flip_x, flip_z, flip_x_z, flip_z_x])
                feature_final.append(np.multiply(mini_batch, random_flip))
            else:
                feature_final.append(mini_batch)
        clf_cnnlstm.fit(np.array(feature_final), targets, epochs=5, batch_size=5)
        self.clf_cnnlstm = clf_cnnlstm

    def predict(self, features):
    	pred_cnnlstm = self.clf_cnnlstm.predict(features)
    	return(pred_cnnlstm)

    def model_info(self):
        clf_cnnlstm = self.model()
        print(clf_cnnlstm.summary())

    def reset(self):
        self.clf_cnnlstm = None

    def save(self, dir_save):
    	self.clf_cnnlstm.save(dir_save + 'cnn_lstm')

def moving_average(arr, window_size):
    i = 0
    # Initialize an empty list to store moving averages
    moving_averages = []
      
    # Loop through the array to consider
    # every window of size 3
    while i < len(arr) - window_size + 1:
        
        # Store elements from i to i+window_size
        # in list to get the current window
        window = arr[i : i + window_size]
      
        # Calculate the average of current window
        window_average = round(sum(window) / window_size, 2)
          
        # Store the average of current
        # window in moving average list
        moving_averages.append(window_average)
          
        # Shift window to right by one position
        i += 1
    return(moving_averages)


def FIR_filter(data, cutoff=1, fs=100, n_taps=512):
    fil = signal.firwin(n_taps, cutoff, pass_zero=False, nyq=fs//2)
    modified_data = signal.filtfilt(fil, 1, data, axis=0)
    return modified_data

def preprocessing(data, data_type='FIC'):
    '''
    Kyritsis et al required preprocessing:
    Input data: input data chosen from three datasets:  FIC, OREBA, and Clemson.
    Required steps:
        1) Hand mirroring: left to right by IMU transforming matrix (implemented in 3 datasets already).
        2) Moving average filter with length = 25.
        3) High-pass finite impulse response (FIR) filter: 1Hz and 512 samples. 
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
    # page 28: sliding window size 5 seconds
    LENGTH = 5 * FREQ 

    train_x_final = []
    valid_x_final = []
    test_x_final = []

    if(data_type == 'FIC'):
        for i in range(train_x.shape[0]/LENGTH):
            # Moving average
            train_x_smooth = moving_average(train_x[i, i + LENGTH], 25)
            # FIR filter
            train_x_final.append(FIR_filter(data=train_x_smooth, cutoff=1, fs=100, n_taps=512).reshape([1,LENGTH,6]))
        for j in range(test_x.shape[0]/LENGTH):
            # Moving average
            test_x_smooth = moving_average(test_x[j, j + LENGTH], 25)
            # FIR filter
            test_x_final.append(FIR_filter(data=test_x_smooth, cutoff=1, fs=100, n_taps=512).reshape([1,LENGTH,6]))
        return(x_train_final, train_y, x_test_final, test_y)
    else:
       for i in range(train_x.shape[0]/LENGTH):
            # Moving average
            train_x_smooth = moving_average(train_x[i, i + LENGTH], 25)
            # FIR filter
            train_x_final.append(FIR_filter(data=train_x_smooth, cutoff=1, fs=100, n_taps=512).reshape([1,LENGTH,6]))
        for j in range(valid_x.shape[0]/LENGTH):
            # Moving average
            valid_x_smooth = moving_average(valid_x[j, j + LENGTH], 25)
            # FIR filter
            valid_x_final.append(FIR_filter(data=valid_x_smooth, cutoff=1, fs=100, n_taps=512).reshape([1,LENGTH,6]))
        for k in range(test_x.shape[0]/LENGTH):
            # Moving average
            test_x_smooth = moving_average(test_x[k, k + LENGTH], 25)
            # FIR filter
            test_x_final.append(FIR_filter(data=test_x_smooth, cutoff=1, fs=100, n_taps=512).reshape([1,LENGTH,6]))
        return(x_train_final, train_y, x_valid_final, valid_y, x_test_final, test_y)