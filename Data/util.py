import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def reliability_small(timeArr, seg, freq):
    '''
    Run reliability test on segments with target sampling frequency.

    :param ndarray timeArr: array of timestamps associated with signal.
    :param float seg: length of the segment in seconds.
    :param int freq: target sampling frequency.

    :return result: average relibility score for the entire time array.
    '''
    time_unique = np.unique(timeArr)
    time_arr = np.sort(time_unique)
    freq_list = []    
    start = time_arr[0]
    while(start < time_arr[-1]):
        end = start + seg # every 'seg' sec        
        count = sum((time_arr < end)&(time_arr >= start))
        perc = count / (freq * seg)
        if(perc >= 1):
            freq_list.append(1)
        else:
            freq_list.append(perc)           
        start = end   
    return(np.mean(freq_list))


def plot_acc(df):
    '''
    Plot signal (matplotlib)

    :param dataframe df: pandas dataframe with signal 'acc_x', 'acc_y', 'acc_z', 'gyr_x', 'gyr_y' and 'gyr_z'.
    '''
    plt.figure(figsize=(10,6))
    plt.plot(df[['time','acc_x']].time, df[['time','acc_x']].acc_x, label='accX')
    plt.plot(df[['time','acc_y']].time, df[['time','acc_y']].acc_y, label='accY')
    plt.plot(df[['time','acc_z']].time, df[['time','acc_z']].acc_z, label='accZ')
    #plt.plot(df[['time','gyr_x']].time, df[['time','gyr_x']].gyr_x, label='gyrX')
    #plt.plot(df[['time','gyr_y']].time, df[['time','gyr_y']].gyr_y, label='gyrY')
    #plt.plot(df[['time','gyr_z']].time, df[['time','gyr_z']].gyr_z, label='gyrZ')
    plt.legend()
    plt.show()


def stats(l):
    '''
    Get basic statistics of the list

    :param 1darray l: list of numbers.

    :return result: min, max, mean and standard deviation of the list.
    '''
    min_l = np.min(l)
    max_l = np.max(l)
    mean_l = np.mean(l)
    std_l = np.std(l)
    return([min_l, max_l, mean_l, std_l])


def outlier(l):
    '''
    Get IQR of the list

    :param 1darray l: list of numbers.

    :return result: low, high, q1 and q3 of the list.
    '''
    q1 = np.percentile(l, 25)  
    q3 = np.percentile(l, 75)
    IQR = q3-q1
    low = q1 - 1.5*IQR
    high = q3+1.5*IQR
    return(low, high, q1, q3)


def resample(dataDf, timeColHeader, samplingRate, gapTolerance=np.inf, fixedTimeColumn=None):
    '''
    Resample signal based on target sampling frequency and gap tolerance.

    :param dataframe dataDf: input dataframe containing column of time and values.
    :param string timeColHeader: name of the time column.
    :param int samplingRate: target sampling frequency.
    :param float gapTolerance: gap tolerance, if exceeds then do not resample the given interval.
    :param array fixedTimeColumn: list of columns that do not need to be resampled.

    :return dataframe dataDf: resampled dataframe.
    '''
    originalNameOrder = list(dataDf.columns.values)
    unixtimeArr = dataDf[timeColHeader].values
    deltaT = 1000.0/samplingRate
    dataDf = dataDf.drop(timeColHeader, axis=1)
    dataArr = dataDf.values
    names = list(dataDf.columns.values)

    n = len(unixtimeArr)
    newDataList = []
    
    if n<2:
        return

    if fixedTimeColumn is None:
        #Looping through columns to apply the resampling method for each column
        for c in range(dataArr.shape[1]):
            signalArr = dataArr[:,c]

            # always take the first timestamp time[0]
            newSignalList = [signalArr[0]]
            newUnixtimeList = [unixtimeArr[0]]

            t = unixtimeArr[0] + deltaT
            tIndAfter = 1

            # iterate through the original signal
            while True:
                # look for the interval that contains 't'
                i0 = tIndAfter
                for i in range(i0,n):# name indBefore/after
                    if  t <= unixtimeArr[i]:#we found the needed time index
                        tIndAfter = i
                        break

                # interpolate in the right interval, gapTolenance=0 means inf tol,
                if gapTolerance == np.inf or \
                    (abs(unixtimeArr[tIndAfter-1]-unixtimeArr[tIndAfter])<=gapTolerance):
                    s = interpolate(unixtimeArr[tIndAfter-1], signalArr[tIndAfter-1], \
                                    unixtimeArr[tIndAfter], signalArr[tIndAfter], t)
                else:
                    s = np.nan

                # apppend the new interpolated sample to the new signal and update the new time vector
                newSignalList.append(s)
                newUnixtimeList.append(int(t))
                # take step further on time
                t = t + deltaT
                # check the stop condition
                if t>unixtimeArr[-1]:
                    break

            newDataList.append(newSignalList)
            newDataArr = np.transpose(np.array(newDataList))

        dataDf = pd.DataFrame(data = newDataArr, columns = names)
        dataDf[timeColHeader] = np.array(newUnixtimeList)

        # change to the original column order
        dataDf = dataDf[originalNameOrder]

    else:  #if fixedTimeColumn not None:
        #Looping through columns to apply the resampling method for each column
        for c in range(dataArr.shape[1]):
            signalArr = dataArr[:,c]
            newSignalList = []
            newUnixtimeList = []

            iFixedTime = 0

            t = fixedTimeColumn[iFixedTime]
            tIndAfter = 0
            outOfRange = 1

            # iterate through the original signal
            while True:
                # look for the interval that contains 't'
                i0 = tIndAfter
                for i in range(i0,n):
                    if  t <= unixtimeArr[i]:#we found the needed time index
                        tIndAfter = i
                        outOfRange = 0
                        break

                if outOfRange:
                    s = np.nan
                else:
                    # interpolate in the right interval
                    if tIndAfter == 0: # means unixtimeArr[0] > t, there is no element smaller than t
                        s = np.nan
                    elif gapTolerance == np.inf or \
                        (abs(unixtimeArr[tIndAfter-1] - unixtimeArr[tIndAfter]) <= gapTolerance):
                        s = interpolate(unixtimeArr[tIndAfter-1], signalArr[tIndAfter-1], \
                                        unixtimeArr[tIndAfter], signalArr[tIndAfter], t)
                    else:
                        s = np.nan

                # apppend the new interpolated sample to the new signal and update the new time vector
                newSignalList.append(s)
                newUnixtimeList.append(int(t))

                # check the stop condition
                if t>unixtimeArr[-1]:
                    break
                # take step further on time
                iFixedTime += 1

                if iFixedTime>=len(fixedTimeColumn):
                    break
                t = fixedTimeColumn[iFixedTime]

            newDataList.append(newSignalList)
            newDataArr = np.transpose(np.array(newDataList))

        dataDf = pd.DataFrame(data = newDataArr, columns = names)
        dataDf[timeColHeader] = np.array(newUnixtimeList)

        # change to the original column order
        dataDf = dataDf[originalNameOrder]
    dataDf = dataDf.dropna(how='any')
    return dataDf

def interpolate(t1, s1, t2, s2, t):
    """
    Interpolates at parameter 't' between points (t1,s1) and (t2,s2)
    """

    if(t1<=t and t<=t2): #we check if 't' is out of bounds (between t1 and t2)
        m = float(s2 - s1)/(t2 - t1)
        b = s1 - m*t1
        return m*t + b
    else:
        return np.nan