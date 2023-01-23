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

with open(PATH) as f:
    dataset = pkl.load(f)

sub = dataset['subject_id'] # for the subject id
ses = dataset['session_id'] # for the session id
raw = dataset['signals_raw'] # for the raw IMU signals
proc = dataset['signals_proc'] # for the processed IMU signals
mm = dataset['mm_gt'] # for the micromovement ground truth
bite = dataset['bite_gt'] # for the bite ground truth

### Statistical Summary
#### by participant
sub_id = [1,2,3,4,5,6,7,8,9,10,11,12]
n_resample = 126
length_all = []
length_time_all = []
reliability_all = []

for eachIdx in range(len(proc)):
    df = pd.DataFrame(proc[eachIdx], columns=['time','acc_x','acc_y','acc_z','gyr_x','gyr_y','gyr_z'])
    label = pd.DataFrame(mm[eachIdx], columns=['start','end','label'])

    # combine up->mouth as feeding gesture
    label_up = label[label['label']==2]
    label_mouth = label[label['label']==5]
    label_down = label[label['label']==3]
    df_feeding = pd.merge(label_up, label_mouth, left_on='end', right_on='start', how='inner')
    df_feeding_2 = pd.merge(df_feeding, label_down, left_on='end_y', right_on='start', how='inner')
    label_feeding = df_feeding_2[['start_x','end']]
    label_feeding.columns= ['start', 'end']
    label_feeding['label'] = 'feeding'

    # extract each feeding episode from labels
    df_list = [] 
    length = []
    time_length = []
    reliability = []
    for index, row in label_feeding.iterrows():
        start = row['start']
        end = row['end']
        data = df[(df['time'] >= start) & (df['time'] <= end)]
        data = data.reset_index(drop=True)
        # check reliability score(0.1s segment, 100Hz) > 0.9
        if(data.shape[0] != 0): #non-empty
            reliability_score = reliability_small(np.array(data['time']), 0.1, 100)
            if(reliability_score > 0.9):
                df_list.append(data)
                length.append(data.shape[0])
                time_length.append(data['time'][data.shape[0]-1] - data['time'][0])
                reliability.append(reliability_score)
            else:
                continue
    length_all.append(length)
    length_time_all.append(time_length)
    reliability_all.append(reliability)
    
sub_id = [1,2,3,4,5,6,7,8,9,10,11,12]
sum_all = []
mean_all = []
std_all = []
for eachId in sub_id:
    idx = [i for i, x in enumerate(sub) if x == eachId]
    time = [length_time_all[index] for index in idx]
    time_flat = [item for sublist in time for item in sublist]
    sum_all.append(round(sum(time_flat),2))
    mean_all.append(round(np.mean(time_flat),2))
    std_all.append(round(np.std(time_flat),2))
    
stats_all = [sub_id, sum_all, mean_all, std_all]
df_stats = pd.DataFrame({'ID':sub_id, 'Total Time(sec)':sum_all, 'Average Time(sec)':mean_all, 'STD Time(sec)':std_all})
flat_length = np.array([item for sublist in length_all for item in sublist])
flat_time = np.array([item for sublist in length_time_all for item in sublist])
flat_reliability = np.array([item for sublist in reliability_all for item in sublist])

stats_1 = ['Length(sec)'] + stats(flat_time)
stats_2 = ['Length(obs)'] + stats(flat_length)
stats_3 = ['Reliability'] + stats(flat_reliability)
stats_all = [stats_1, stats_2, stats_3]
df_stats = pd.DataFrame(stats_all, columns=['Name', 'Min', 'Max', 'Mean', 'STD'])

low, high, q1, q3= outlier(flat_length)
mean_len = int(np.mean(flat_length[(flat_length>low) & (flat_length<high)]))
print('Length - Q1:',q1)
print('Length - Q3:',q3)
print('Length - mean(outliers excluded):',mean_len)
print(df_stats[['Name','Mean','STD']])


# start resample and save the training data
resample_all = []

# for 3 different resample lengths
for resample_len in [int(q1),int(mean_len),int(q3)]:
    sub_id = [1,2,3,4,5,6,7,8,9,10,11,12]
    x_others_train_all = []
    x_feeding_train_all = []
    y_others_train_all = []
    y_feeding_train_all = []
    x_test_all = []
    label_testing_all = []
    print('processing length:', resample_len)
    
    count_below = 0
    
    # for each session/meal
    for eachIdx in range(len(proc)):
        df = pd.DataFrame(proc[eachIdx], columns=['time','acc_x','acc_y','acc_z','gyr_x','gyr_y','gyr_z'])
        label = pd.DataFrame(mm[eachIdx], columns=['start','end','label'])
        print('session:', eachIdx)
        # Exponential Moving Average
        df_ewm = df.ewm(com=0.2).mean() 

        # combine up->mouth->down as feeding gesture
        label_up = label[label['label']==2]
        label_mouth = label[label['label']==5]
        label_down = label[label['label']==3]
        df_feeding = pd.merge(label_up, label_mouth, left_on='end', right_on='start', how='inner')
        df_feeding_2 = pd.merge(df_feeding, label_down, left_on='end_y', right_on='start', how='inner')
        label_feeding = df_feeding_2[['start_x','end']]
        label_feeding.columns= ['start', 'end']
        label_feeding['label'] = 'feeding'
        total = total + label_up.shape[0]
        after = after + label_feeding.shape[0]

        # using the entire session as training
        train_label = label_feeding
        train_label = train_label.reset_index(drop = True)
        df_train_all = df 
        df_train_all = df_train_all.reset_index(drop = True)

        ###### Trianing ######
        ### extract non-feeding episodes from training
        df_others_list = []
        df_others_1 = df_train_all[df_train_all['time'] < train_label['start'][0]]
        df_others_1 = df_others_1.reset_index(drop=True)
        df_others_list.append(df_others_1)

        for i in range(train_label.shape[0]-1):
            start = train_label['end'][i]
            end = train_label['start'][i+1]
            data = df_train_all[(df_train_all['time'] >= start) & (df_train_all['time'] < end)]
            data = data.reset_index(drop=True)
            
            if(data.shape[0] > 0):
                # check reliability score(0.1s segment, 100Hz) > 0.8
                reliability_score = reliability_small(np.array(data['time']), 0.1, 100)
                if(reliability_score > 0.8):
                    df_others_list.append(data)

        # resample non-feeding from training
        df_others = []
        for bigSeg in df_others_list:
            for i in range(0, bigSeg.shape[0], resample_len):
                smallSeg = bigSeg.loc[i:i+resample_len-1]
                smallSeg = smallSeg.reset_index(drop=True)
                if(smallSeg.shape[0] == resample_len):
                    df_others.append(smallSeg)

        # get the array form of x_train_others
        x_others_final = []
        for each in df_others:
            x_others_final.append(np.array(each)[:,1:7])
        
        x_others_train_all.append(np.array(x_others_final)) # save each session to all
        y_others_train_all.append([0]*len(np.array(x_others_final)))
        
        
        ### extract each feeding episode from labels
        df_list = [] 
        for index, row in train_label.iterrows():
            start = row['start']
            end = row['end']
            data = df[(df['time'] >= start) & (df['time'] <= end)]
            data = data.reset_index(drop=True)
            # check reliability score(0.1s segment, 100Hz) > 0.8
            if((data.shape[0] != 0) & (data.shape[0] <= high) & (data.shape[0] >= low)): #non-empty and non-outliers 
                reliability_score = reliability_small(np.array(data['time']), 0.1, 100)
                if(reliability_score > 0.8):
                    df_list.append(data)

        # resample each to resample_len
        df_resampled_list = []
        for i in range(len(df_list)):
            df_temp = df_list[i].copy()
            df_temp['time'] = df_temp['time'] * 1000
            df_resampled = resample(df_temp, 'time', (resample_len+3)/df_temp.shape[0]*100, gapTolerance=np.inf)
            if(df_resampled.head(resample_len).shape[0]==resample_len):

            	#L2 normalization
            	normalized = preprocessing.normalize(df_resampled.head(resample_len), norm='l2')
                df_resampled_list.append(df_resampled.head(normalized))
        
        # convert to numpy array
        x_feeding_final = []
        for each in df_resampled_list:
            x_feeding_final.append(np.array(each)[:,1:7])    
        x_feeding_train_all.append(np.array(x_feeding_final))
        y_feeding_train_all.append([1]*len(np.array(x_feeding_final)))

        ###### Testing ######
        #get entire session from first feeding to last feeding segment
        df_test_all = df[df['time'] <= label_feeding['end'][label_feeding.shape[0]-1]] 
        df_test_all = df_test_all.reset_index(drop=True)
        x_test_all.append(df_test_all)
        label_testing_all.append(train_label)
    
    # merge feeding and non-feeding together 
    x_train_all = []
    y_train_all = []
    
    for i in range(len(x_feeding_train_all)):
        x_train_temp = np.concatenate((x_feeding_train_all[i], x_others_train_all[i]), axis=0)
        y_train_temp = y_feeding_train_all[i] + y_others_train_all[i]
        x_train_all.append(x_train_temp)
        y_train_all.append(y_train_temp)
    
    # save train/test split by session
    FIC_train = {
    "x_train_all": x_train_all,
    "y_train_all": y_train_all,
    "x_test_all": x_test_all, # by sesson
    "y_test_all": label_testing_all,
    "subject": sub
    }
    
    resample_all.append(FIC_train)

save_names = ['train_q1_LOSO.pkl', 'train_mean_LOSO.pkl', 'train_q3_LOSO.pkl']
for i in range(len(save_names)):
    full_name = PATH_SAVE + save_names[i]
    with open(full_name,'wb') as f:
        pkl.dump(resample_all[i], f)
        
# Total number of feeding and non-feeding
count_1 = 0
count_0 = 0
for i in range(len(resample_all[1]['y_train_all'])):
    count_1 = count_1 + np.sum(resample_all[1]['y_train_all'][i])
    count_0 = count_0 + len(resample_all[1]['y_train_all'][i]) - np.sum(resample_all[1]['y_train_all'][i])
print('Feeding',count_1)
print('Non-feeding',count_0)