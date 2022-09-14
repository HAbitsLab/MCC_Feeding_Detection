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

sub_id = [4,7,10,11,12,13,14,17,18,23,24]
length_all = []
length_time_all = []
reliability_all = []
labels_count = []
labels_count_below = []

for i in range(len(sub_id)):
    df_raw = pd.read_csv(PATH + 'raw_data/P' + str(sub_id[i]) + '_raw.csv')
    label = pd.read_csv(PATH + + 'annotations/P' + str(sub_id[i]) + '_all/gesture_bandtime.csv')
    label['StartTime'] = pd.to_datetime(label['StartTime']).dt.tz_localize(None)
    label['EndTime'] = pd.to_datetime(label['EndTime']).dt.tz_localize(None)
    df = watch_add_datetime(df_raw)
    df.columns = ['index','acc_x','gyro_x','acc_y','unix_time','gyro_z','gyro_y','acc_z','time']
    label.columns = ['start','end','label']

    # extract each feeding episode from labels
    df_list = [] 
    length = []
    time_length = []
    reliability = []
    count = 0
    count_below = 0
    for index, row in label.iterrows():
        start = row['start']
        end = row['end']
        data = df[(df['time'] >= start) & (df['time'] <= end)]
        data = data.reset_index(drop=True)
        # check reliability score(0.1s segment, 100Hz) > 0.8
        if(data.shape[0] != 0): #non-empty
            time_array = np.array(data['time'].values.astype(float)/10**9)
            reliability_score = reliability_small(time_array, 0.1, 30)
            if(reliability_score > 0.9):
                df_list.append(data)
                length.append(data.shape[0])
                time_length.append(time_array[data.shape[0]-1] - time_array[0])
                reliability.append(reliability_score)
                count = count + 1
            else:
                #print('reliability score < 0.9')
                count_below = count_below + 1
    labels_count.append(count)
    labels_count_below.append(count_below)
    length_all.append(length)
    length_time_all.append(time_length)
    reliability_all.append(reliability)

sub_id = [4,7,10,11,12,13,14,17,18,23,24]
sum_all = []
mean_all = []
std_all = []

for idx in range(len(sub_id)):
    length_p = length_all[idx]
    length_time_p = length_time_all[idx]
    sum_all.append(round(sum(length_time_p),2))
    mean_all.append(round(np.mean(length_time_p),2))
    std_all.append(round(np.std(length_time_p),2))
    
stats_all = [sub_id, sum_all, mean_all, std_all]
print('Total reliable feeding gestures:', sum(labels_count))
print('Percentage of reliable gestures (> 0.9)', sum(labels_count)/(sum(labels_count)+sum(labels_count_below)))
print(pd.DataFrame({'ID':sub_id, 'Total Time(sec)':sum_all, 'Average Time(sec)':mean_all, 'STD Time(sec)':std_all, 'Reliable Labels':labels_count, 'Unreliable Labels': labels_count_below}))

flat_length = np.array([item for sublist in length_all for item in sublist])
flat_time = np.array([item for sublist in length_time_all for item in sublist])
flat_reliability = np.array([item for sublist in reliability_all for item in sublist])

stats_1 = ['Length(sec)'] + stats(flat_time)
stats_2 = ['Length(obs)'] + stats(flat_length)
stats_3 = ['Reliability'] + stats(flat_reliability)
stats_all = [stats_1, stats_2, stats_3]
pd.DataFrame(stats_all, columns=['Name', 'Min', 'Max', 'Mean', 'STD'])

### TODO: process data based on target sliding window length