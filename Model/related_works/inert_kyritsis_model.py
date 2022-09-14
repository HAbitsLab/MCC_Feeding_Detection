import numpy as np
from tensorflow.keras.layers import Dense, MaxPooling1D, LSTM, Flatten, Dropout, Conv1D, TimeDistributed, BatchNormalization
from tensorflow.keras.wrappers.scikit_learn import KerasClassifier
from tensorflow.keras.models import Sequential
from sklearn.model_selection import StratifiedKFold, cross_val_score
from keras.optimizers import RMSprop, Adam
from scipy.stats import *
from numpy import *
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
        clf_cnnlstm.fit(features, targets, epochs=5, batch_size=5)
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