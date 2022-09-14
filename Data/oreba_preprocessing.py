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

def get_intake_label(df_clean):
    '''
    Extract intake gesture labels (dominant and non-dominant hands) from the processed dataset.

    :param dataframe df_clean: processed dataframe.

    :return dataframe label_all: intake labels for the input dataframe.
    '''

    dom_hand = list(set(df_clean['dom_hand']))[0].capitalize()
    df_intake = df_clean[(df_clean['label_1']=='Intake')&((df_clean['label_3']==dom_hand)|(df_clean['label_3']=='Both'))]
    start = []
    end = []
    list_frame = list(df_intake['frame_id'])
    start.append(list_frame[0])
    for i in range(len(list_frame)-1):
        if((list_frame[i+1] - list_frame[i]) == 1):
            continue
        else:
            end.append(list_frame[i])
            start.append(list_frame[i+1])
    end.append(list_frame[-1])
    label_intake = pd.DataFrame({'start':start, 'end':end, 'label':['Inatke-dom']*len(start)})
    
    if(dom_hand == 'Right'):
        non_dom = 'Left'
    else:
        non_dom = 'Right'
        
    df_intake_nondom = df_clean[(df_clean['label_1']=='Intake')&((df_clean['label_3']==non_dom))]
    if(df_intake_nondom.shape[0] > 0):
        start = []
        end = []
        list_frame = list(df_intake_nondom['frame_id'])
        start.append(list_frame[0])
        for i in range(len(list_frame)-1):
            if((list_frame[i+1] - list_frame[i]) == 1):
                continue
            else:
                end.append(list_frame[i])
                start.append(list_frame[i+1])
        end.append(list_frame[-1])
        label_intake_nondom = pd.DataFrame({'start':start, 'end':end, 'label':['Inatke-nondom']*len(start)})

        label_all = pd.concat([label_intake, label_intake_nondom]).reset_index(drop=True)
    else:
        label_all = label_intake
    
    return(label_all)


def extract_train_test(df_raw, df_label, resample_len, freq):
    '''
    Extract train and text from the original dataset.

    :param dataframe df_raw: raw dataframe.
    :param dataframe df_label: label of feeding and non-feeding.
    :param int resample_len: length of the segment after resampling.
    :param int freq: target sampling frequency.

    :return result: training x, y, test x and y dataframes (entire).
    '''

    df_label = df_label.sort_values(by=['start']).reset_index(drop=True)
    df_raw = df_raw[['frame_id','timestamp','dom_acc_x','dom_acc_y','dom_acc_z','dom_gyro_x','dom_gyro_y','dom_gyro_z',
                     'ndom_acc_x', 'ndom_acc_y', 'ndom_acc_z', 'ndom_gyro_x', 'ndom_gyro_y', 'ndom_gyro_z']]
    # flip non-dominant hand
    df_raw['ndom_gyro_x'] = df_raw['ndom_gyro_x'] * -1
    df_raw['ndom_gyro_y'] = df_raw['ndom_gyro_y'] * -1
    df_raw['ndom_acc_x'] = df_raw['ndom_acc_x'] * -1
    df_raw['ndom_acc_y'] = df_raw['ndom_acc_y'] * -1
    
    label_intake = df_label

    # process the data for train and test by session
    x_train = []; y_train = []; x_test = []; y_test = []
    df = df_raw

    ### Processing Training Set
    # for all intake gestures (bite)
    for index, row in label_intake.iterrows():
        start = row['start']
        end = row['end']
        data = df[(df['frame_id']>=start)&(df['frame_id']<=end)].reset_index(drop=True)

        # resize length into 2.41s * 64Hz = 154 
        
        if(row['label']=='Inatke-dom'):
            df_temp = data.iloc[:,3:9]
        else:
            df_temp = data.iloc[:,9:15] # non-dominant hand
            
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
    if(df[df['frame_id']<label_intake['start'][0]].shape[0] >= resample_len):
        x_test_temp.append(df[df['frame_id']<label_intake['start'][0]].reset_index(drop=True))  
    for i in range(label_intake.shape[0]-1):
        start = label_intake['end'][i]
        end = label_intake['start'][i+1]
        data = df[(df['frame_id']>=start)&(df['frame_id']<=end)].reset_index(drop=True)
        if(data.shape[0] >= resample_len):
            x_test_temp.append(data)
    for bigSeg in x_test_temp:
        for i in range(0, bigSeg.shape[0], resample_len):
            smallSeg = bigSeg.loc[i:i+resample_len-1]
            smallSeg = smallSeg.reset_index(drop=True)
            if(smallSeg.shape[0] == resample_len):
                x_train.append(np.array(smallSeg)[:,2:8])
                y_train.append(0)

    ### Processing Testing Set
    x_test.append(df)
    y_test.append(label_intake)
    
    return([np.array(x_train), np.array(y_train), x_test, y_test])

dir_path = os.path.dirname(PATH)
participants = os.listdir(dir_path)
p_data = {key: [] for key in participants}

length = []
count_intake = 0
count_nonintake = 0
resample_len = 154 # resize shape (mean)
freq = 64 # sampling frequency
count = 0

for p in participants:
    print('Processing:', p)
    df_raw = pd.read_csv(PATH +str(p)+'/' + str(p) + '_inertial_processed.csv')
    df_label = get_intake_label(df_raw)
    
    for index, row in df_label.iterrows():
        start = row['start']
        end = row['end']
        data = df_clean[(df_clean['frame_id']>=start)&(df_clean['frame_id']<=end)]
        data = data.reset_index(drop=True)
        if(data.shape[0] != 0): #non-empty
            length.append(data.shape[0])
            count = count + 1
    p_data[p].append(extract_train_test(df_raw, df_label, resample_len, freq))
    count_intake = count_intake + sum(extract_train_test(df_raw, df_label, resample_len, freq)[1] == 1)
    count_nonintake = count_nonintake + sum(extract_train_test(df_raw, df_label, resample_len, freq)[1] == 0)

with open(PATH_SAVE,'wb') as f:
    pkl.dump(p_data, f)