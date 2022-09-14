import pandas as pd
import numpy as np
import pickle as pkl
import scipy
import seaborn as sns
import warnings
import timeit
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from sklearn import preprocessing
from util import reliability_small, stats, resample, plot_acc, outlier

def extract_train_test(df_raw, df_label, resample_len, freq):
    '''
    Extract train and text from the original dataset.

    :param dataframe df_raw: raw dataframe.
    :param dataframe df_label: label of feeding and non-feeding.
    :param int resample_len: length of the segment after resampling.
    :param int freq: target sampling frequency.

    :return result: training x, y, test x and y dataframes (entire).
    '''

    # gyro x/y/z = yaw, pitch, roll
    df_raw.columns = ['acc_x','acc_y','acc_z','gyro_x','gyro_y','gyro_z','scale']
    df_label.columns = ['label', 'start', 'end']

    # process the data for train and test by session
    x_train = []; y_train = []; x_test = []; y_test = []
    df = df_raw

    ### Processing Training Set
    # for all intake gestures (bite)
    label_intake = df_label[df_label['label']=='bite'].reset_index(drop=True)
    for index, row in label_intake.iterrows():
        start = row['start']
        end = row['end']
        data = df.loc[start:end]
        data = data.reset_index(drop=True)   

        # resize length into 2.2s * 15Hz = 33 
        df_temp = data
        time_temp = np.arange(1/freq, df_temp.shape[0]/freq+10/freq, 1/freq) * 1000
        time_temp = time_temp[0:df_temp.shape[0]]
        df_temp['time'] = time_temp
        df_resize = resample(df_temp, 'time', (resample_len+2)/(df_temp.shape[0]/freq), gapTolerance=np.inf)
        df_resize = df_resize.loc[0:resample_len-1]

        # add x_train, y_train = intake (1)
        x_train.append(preprocessing.normalize(np.array(df_resize)[:,0:6], norm='l2')) #L2 normalization
        y_train.append(1)

    # for all other gestures (non-bite)
    x_test_temp = []
    if(df.loc[0:label_intake['start'][0]].shape[0] >= resample_len):
        x_test_temp.append(df.loc[0:label_intake['start'][0]].reset_index(drop=True))  
    for i in range(label_intake.shape[0]-1):
        start = label_intake['end'][i]
        end = label_intake['start'][i+1]
        data = df.loc[start:end].reset_index(drop=True)
        if(data.shape[0] >= resample_len):
            x_test_temp.append(data)
    for bigSeg in x_test_temp:
        for i in range(0, bigSeg.shape[0], resample_len):
            smallSeg = bigSeg.loc[i:i+resample_len-1]
            smallSeg = smallSeg.reset_index(drop=True)
            if(smallSeg.shape[0] == resample_len):
                x_train.append(np.array(smallSeg)[:,0:6])
                y_train.append(0)

    ### Processing Testing Set
    x_test.append(df)
    y_test.append(label_intake)
    return([np.array(x_train), np.array(y_train), x_test, y_test])

dir_path = os.path.dirname(PATH + 'all-gt-gestures/')
participants = os.listdir(dir_path)
p_data = {key: [] for key in participants}

length = []
count_intake = 0
count_nonintake = 0
resample_len = 33 # resize shape (mean)
freq = 15 # sampling frequency

for p in participants:
    files = os.listdir(PATH + 'all-gt-gestures/'+str(p)+'/')
    for each_session in files:
        print('Processing: Participant', p, 'Session:', each_session)
        path_session = os.listdir(PATH +'all-data/'+str(p)+'/'+each_session)
        #try: # if a session has annotation
        df_raw = pd.read_csv(PATH +'all-data/'+str(p)+'/'+each_session+'/'+path_session[0], sep='\t', header=None)
        df_label = pd.read_csv(PATH +'all-gt-gestures/'+str(p)+'/'+each_session+'/gesture_union.txt', sep='\t', header=None)
        df_label = df_label.iloc[:, 0:3] # sanity check
        df_raw.columns = ['acc_x','acc_y','acc_z','gyro_x','gyro_y','gyro_z','scale']
        df_label.columns = ['label', 'start', 'end']
        label = df_label[df_label['label']=='bite']

        for index, row in label.iterrows():
            start = row['start']
            end = row['end']
            data = df_raw.loc[start:end]
            data = data.reset_index(drop=True)
            if(data.shape[0] != 0): #non-empty
                length.append(data.shape[0])
                count = count + 1
        p_data[p].append(extract_train_test(df_raw, df_label, resample_len, freq))
        count_intake = count_intake + sum(extract_train_test(df_raw, df_label, resample_len, freq)[1] == 1)
        count_nonintake = count_nonintake + sum(extract_train_test(df_raw, df_label, resample_len, freq)[1] == 0)

with open(PATH_SAVE,'wb') as f:
    pkl.dump(p_data, f)