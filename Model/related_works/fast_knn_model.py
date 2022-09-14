"""
Algorithm training steps:

(1) Select a similarity measure and create a similarity matrix from the given training dataset.

(2) Set to ‘ungrouped’ the tag of all data tuples.

(3) For each ‘ungrouped’ data tuple, find its largest local neighbourhood which covers the largest number of neighbours with the same category.

(4) Find the data tuple di with a largest global neighbourhood Ni among all the local neighbourhoods, create a representative <Cls(di), Sim(di), 
Num(di), Rep(di)> into M to represent all the data tuples covered by Ni, and then set to ‘grouped’ the tag of all the data tuples covered by Ni.

(5) Repeat step 3 and step 4 until all the data tuples in the training dataset have been set to ‘grouped’.

(6) Model M consists of all the representatives collected from the above learning process.


Algorithm test steps:

(1) For a new data tuple dt to be classified, calculate its similarity to all representatives in the model M.

(2) If dt is covered only by one representative <Cls(dj), Sim(dj), Num(dj), Rep(dj)>, viz the Euclidean distance of dt to dj is smaller than 
Sim(dj), dt is classified as the category of dj.

(3) If dt is covered by at least two representatives with different category, classify dt as the category of the representative with largest 
Num(dj), viz. the neighbourhood covers the largest number of data tuples in the training dataset.

(4) If no representative in the model M covers dt, classify dt as the category of a representative which boundary is closest to dt.

"""

import random
import copy
import seaborn as sns
import numpy as np
import pandas as pd
import timeit
import pickle
from pathlib import Path
from matplotlib import pyplot as plt
from sklearn.metrics import classification_report
from sklearn.metrics import accuracy_score
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.preprocessing import MinMaxScaler
import seaborn as sns
from cdtw import dtw


def plt_centers_thresholds_cluster(data_list, label_list, centers, thresholds):
    import seaborn as sns
    X = []
    y = []
    for features, label in zip(data_list, label_list):
        X.append(features)
        y.append(label)
    X = np.array(X)
    y = np.array(y).flatten()

    figure, axes = plt.subplots()
    sns.scatterplot(X[:,0],X[:,1],hue=y[:],ax=axes)
    for i in range(len(thresholds)-1):
        draw_circle = plt.Circle((centers[i][0], centers[i][1]), thresholds[i], alpha=0.1, fc='yellow')
        axes.add_artist(draw_circle)
        plt.scatter(centers[i][0], centers[i][1], marker='^', c='k')
    draw_circle = plt.Circle((centers[-1][0], centers[-1][1]), thresholds[-1], alpha=0.1, fc='yellow')
    axes.add_artist(draw_circle)
    plt.scatter(centers[-1][0], centers[-1][1], marker='^', c='g')
    plt.xlim((-5,5))
    plt.ylim((-6,6))
    plt.title('centers and thresholds')
    plt.show()


class KNNModel(object):
    """ KNN_Model-Based Classification

    ref: https://www.researchgate.net/publication/221549123_KNN_Model-Based_Approach_in_Classification
    Parameters
    ------------
    
    Attributes
    -----------
    
    """
    # def __init__(self, metric, test_data_list, test_label_list):
    def __init__(self, metric, tolerant=1, tiny_blob_ignored=1): #seed_mode="costest" or "random"
        assert metric in ["euclidean", "dtw"]
        self.metric = metric
        self.f1 = 0
        self.tolerant = tolerant
        assert tiny_blob_ignored > 0
        self.tiny_blob_ignored = tiny_blob_ignored

        self.clusters_info = []
        self.classes = []
        self.centers = []
        self.numbers_covered = []
        self.thresholds = []

    def _instantiate(self, train_data_list, train_label_list):
        instances = []
        for data, label in zip(train_data_list, train_label_list):
            instances.append(Instance(data, label))
        return instances

    def _distance(self, vector1, vector2):   
        if self.metric == 'euclidean':
            return self._eucl(vector1, vector2)
        elif self.metric == 'dtw':
            return self._dtw(vector1, vector2)
        else:
            print('metric must be either euclidean (default) or dtw.')
            exit()

    def _eucl(self, vector1, vector2):   # calculate Euclidean distance  
        return np.sqrt(np.sum(np.power(vector2 - vector1, 2)))
   
    def _dtw(self, vector1, vector2):   # calculate dtw distance  
        return dtw(vector1, vector2)

    def _get_largest_neighborhood_i(self, this_dist, labels, i):
        sorted_dist_label = sorted(zip(this_dist, labels), reverse=False)  # from smallest to largest
        this_label = sorted_dist_label[0][1]
        tmp_i = 1
        noisy_sample = 0
        while noisy_sample <= self.tolerant:
            if sorted_dist_label[tmp_i][1] == this_label:
                tmp_i += 1
            else:
                tmp_i += 1
                noisy_sample += 1

        return tmp_i

    def _get_largest_neighborhood(self, dist_mat, labels):
        """
        # return the number of largest neighborhood for each smaple 
        """
        largest_neighborhood = np.zeros_like(labels)
        for i in range(len(labels)):  # go through all the samples
            this_dist = dist_mat[i,:]
            largest_neighborhood[i] = self._get_largest_neighborhood_i(this_dist, labels, i)

        return largest_neighborhood

    def _get_the_ungrouped_largest_blob(self, state_grouped, labels, largest_neighborhood, dist_mat):
        """
        get the largest blob centered by the data sample from ungrouped samples
        
        """
        largest_nbh = np.copy(largest_neighborhood)

        # set the largest_nbh cell of grouped samples as 0
        largest_nbh = np.multiply(1-state_grouped, largest_nbh) 

        # start from largest blob and set states of covered sample to grouped
        rank_largest_nbh = np.argsort(largest_nbh)[::-1]  # from largest blob to smallest blob

        center_ind = rank_largest_nbh[0]
        num_covered = int(largest_nbh[center_ind])
        this_dist = dist_mat[center_ind]
        sample_covered_ind = np.argsort(this_dist)[:num_covered]

        radius = this_dist[sample_covered_ind[-1]]
        for i in sample_covered_ind:
            state_grouped[i] = 1

        this_cls = labels[center_ind]

        return state_grouped, center_ind, radius, num_covered, this_cls

    def train(self, train_data_list, train_label_list, save_name="knnmodel.sav"):
        """
        # tiny_blob_ignored 
        
        """
        num = len(train_data_list)
        dist_mat = np.zeros((num, num))
        state_grouped = np.zeros((num))  # 0: ungrouped, 1: grouped
        labels = np.zeros((num))  # 0: ungrouped, 1: grouped

        n_pos = 0
        n_neg = 0
        for i, l in enumerate(train_label_list):
            if l == 0:
                n_neg += 1
            elif l == 1:
                n_pos += 1
                labels[i] = 1
            else:
                print("label must be either 0 or 1")
                exit()
        print("# positives:", n_pos)
        print("# negatives:", n_neg)

        print("start training")

        # calculate the (N-1)*N/2 different distances
        for i, feat1 in enumerate(train_data_list):
            for j, feat2 in enumerate(train_data_list):
                if j > i:
                    dist_mat[i,j] = self._distance(feat1, feat2)

        # make a full matrix
        for i, feat1 in enumerate(train_data_list):
            for j, feat2 in enumerate(train_data_list):
                if j < i:
                    dist_mat[i,j] = dist_mat[j,i]

        largest_neighborhood = self._get_largest_neighborhood(dist_mat, labels)
        next_state_grouped, next_center_ind, next_radius, next_num_covered, next_cls = self._get_the_ungrouped_largest_blob(
            state_grouped, labels, largest_neighborhood, dist_mat)

        while next_radius > self.tiny_blob_ignored:
            state_grouped, center_ind, radius, num_covered, this_cls = next_state_grouped, next_center_ind, next_radius, \
                next_num_covered, next_cls
            self.clusters_info.append([this_cls, radius, num_covered, train_data_list[center_ind]])
            next_state_grouped, next_center_ind, next_radius, next_num_covered, next_cls = self._get_the_ungrouped_largest_blob(
                state_grouped, labels, largest_neighborhood, dist_mat)

        self.centers = []
        self.classes = []
        self.thresholds = []
        self.numbers_covered = []
        for cluster in self.clusters_info:
            self.classes.append(cluster[0])
            self.thresholds.append(cluster[1])
            self.numbers_covered.append(cluster[2])
            self.centers.append(cluster[3])

        print("# clusters:", len(self.clusters_info))
        plt_centers_thresholds_cluster(train_data_list, train_label_list, self.centers, self.thresholds)

    def test(self, test_data_list, test_label_list, print_result=0):
        predictions = []
        for data in test_data_list:
            predictions.append(self.pred_instance(data))
        if print_result:
            print(classification_report(test_label_list, predictions, target_names=['negative', 'positive']))

        return accuracy_score(test_label_list, predictions)

    def pred_instance(self, data):
        pred = 0
        num_fallin_clusters = 0
        hit_classes = []
        hit_centers = []
        hit_thresholds = []
        hit_num_covered = []

        for this_class, center, thre, num in zip(self.classes, self.centers, self.thresholds, self.numbers_covered):
            if self._distance(data, center) <= thre:
                hit_classes.append(this_class)
                hit_centers.append(center)
                hit_thresholds.append(thre)
                hit_num_covered.append(num)
                num_fallin_clusters += 1

        if num_fallin_clusters == 1:
            return hit_classes[0]
        elif num_fallin_clusters > 1:
            return sorted(zip(hit_num_covered, hit_classes), reverse=True)[0][1]  # from largest to smallest
        else: # num_fallin_clusters==0
            dist_thres = []
            for this_class, center, thre, num in zip(self.classes, self.centers, self.thresholds, self.numbers_covered):
                dist_thres.append(self._distance(data, center) - thre)
            return sorted(zip(dist_thres, self.classes), reverse=True)[0][1]



def snowman(viz=False):
    xy = pd.read_csv("synthetic_snowman_clusters.csv")
    xy = xy[["x1", "x2", "y"]]
    xy = xy.iloc[::15]

    print("total dataset size:", len(xy))

    X = xy[["x1", "x2"]].values
    y = xy[["y"]].values

    print(X[:,0].shape)
    print(y.shape)

    if viz:
        f, (ax1) = plt.subplots(nrows=1, ncols=1,figsize=(8,8))
        sns.scatterplot(X[:,0],X[:,1],hue=y[:,0],ax=ax1);
        plt.show()

    test_ind = np.random.rand(len(xy)) < 0.3
    xy_train = xy.iloc[~test_ind]
    xy_test = xy.iloc[test_ind]

    # visualize_2d(xy[["x1", "x2"]].values, xy[["y"]].values.reshape(-1))
    
    train_data_list = []
    train_label_list = []
    test_data_list = []
    test_label_list = []

    for i in range(len(xy_train)):
        train_data_list.append(xy_train[["x1", "x2"]].iloc[i].values)
        train_label_list.append(xy_train[["y"]].iloc[i].values)

    for i in range(len(xy_test)):
        test_data_list.append(xy_test[["x1", "x2"]].iloc[i].values)
        test_label_list.append(xy_test[["y"]].iloc[i].values)
        # instances.append(Instance(xy[["x1", "x2"]].iloc[i].values, xy[["y"]].iloc[i].values))
    
    start = timeit.default_timer()
    print("starrt mcc")
    clf = KNNModel(metric="euclidean")
    clf.train(train_data_list, train_label_list)
    print('MCClassifier training time: ', timeit.default_timer() - start)

    start = timeit.default_timer()
    for i in range(1):
    # for i in range(1000):
        accuracy = clf.test(test_data_list, test_label_list, print_result=0)
    print('MCClassifier test time: ', timeit.default_timer() - start)
    print("MCClassifier test accuracy:", accuracy)


if __name__ == '__main__':
    snowman()

