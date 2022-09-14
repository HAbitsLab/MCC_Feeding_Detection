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

from datastruct import Instance, Cluster
from discrepancy_clustering import DiscrepancyClustering
from mcc_baselines import tsLearnKNNClassifier
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")


names = [
    "Nearest Neighbors (N=1)", 
    "Nearest Neighbors (N=3)", 
    "Linear SVM", 
    "RBF SVM",
    "Gaussian Process",
    "Decision Tree", 
    "Random Forest", 
    "Neural Net", 
    "AdaBoost",
    "Naive Bayes", 
    "QDA"]

classifiers = [
    KNeighborsClassifier(1),
    KNeighborsClassifier(3),
    SVC(kernel="linear", C=0.025),
    SVC(gamma=2, C=1),
    GaussianProcessClassifier(1.0 * RBF(1.0)),
    DecisionTreeClassifier(max_depth=5),
    RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1),
    MLPClassifier(alpha=1, max_iter=1000),
    AdaBoostClassifier(),
    GaussianNB(),
    QuadraticDiscriminantAnalysis()]



def plt_centers_thresholds_cluster(enable, instances, centers, thresholds):
    if enable:
        import seaborn as sns
        X = []
        y = []
        for ins in instances:
            X.append(ins.features)
            y.append(ins.label)
        X = np.array(X)
        y = np.array(y)

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
    else:
        return


def print_duplicates(a):
    import collections
    print([item for item, count in collections.Counter(a).items() if count > 1])
    
    
class MCClassifier(object):
    """ multi-centroid classifier
    Parameters
    ------------
    
    Attributes
    -----------
    
    """
    # def __init__(self, metric, test_data_list, test_label_list):
    def __init__(self, metric, seed_mode="random"): #seed_mode="costest" or "random"
        assert metric in ["euclidean", "dtw"]
        self.seed_mode = seed_mode
        self.metric = metric
        self.f1 = 0
        # self.test_data_list = test_data_list
        # self.test_label_list = test_label_list

    def _instantiate(self, train_list, train_label_list):
        instances = []
        for data, label in zip(train_list, train_label_list):
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

    # def _sum_cost(self):
    #     sum_cost = 0
    #     ind_highest_cost = 0        
    #     for i, c in enumerate(self.new_clusters):
    #         cost = c.calc_cost()
    #         sum_cost += cost
    #         if cost > ind_highest_cost:
    #             ind_highest_cost = i
    #     return sum_cost, ind_highest_cost            

    def train(self, train_list, train_label_list, stop_criterion, max_centers=30, early_save=0, \
        save_name="early_save.sav"):
        print("start training")
        self.instances = self._instantiate(train_list, train_label_list)
        self.stop_criterion = stop_criterion

        self.clustering = DiscrepancyClustering(self.instances, metric=self.metric)
        print("training instances", self.clustering.num_instances)

        init_centers = self.clustering.init_centers(1)
        self.centers, self.thres, precision = self.clustering.cluster(init_centers)
        print("# clusters:", len(self.centers), ", precision:", precision)
        plt_centers_thresholds_cluster(0, self.instances, self.centers, self.thres)

        history_best_centers = self.centers
        history_best_thres = self.thres
        history_best_precision = precision

        while precision < self.stop_criterion:
            start = timeit.default_timer()
            new_centers = self.clustering.updated_centers(seed_mode=self.seed_mode)
            self.centers, self.thres, precision = self.clustering.cluster(new_centers)
            print("# clusters:", len(self.centers), ", precision:", precision)
            # print('elapsed time: ', timeit.default_timer() - start)
            # self.test(self.test_data_list, self.test_label_list)  # debug, show test result for each iter
            print("thres", [round(t,2) for t in self.thres])

            # ============ record history best model
            if precision > history_best_precision:
                history_best_precision = precision
                history_best_centers = self.centers
                history_best_thres = self.thres
                if early_save:
                    pickle.dump([self.centers, self.thres], open(save_name, 'wb'))


            # ============ stop training when excedingly clusters are used
            if len(self.centers) >= int(0.5*self.clustering.num_pos_instances):
                break
            if len(self.centers) >= max_centers:
                break

        self.centers = history_best_centers
        self.thres = history_best_thres
        plt_centers_thresholds_cluster(0, self.instances, self.centers, self.thres)
        print("history_best_precision:", history_best_precision)

        return self.centers, self.thres, history_best_precision
        
    def test(self, test_data_list, test_label_list, print_result=0):
        predictions = []
        for data in test_data_list:
            predictions.append(self.pred_instance(data))
        if print_result:
            print(classification_report(test_label_list, predictions, target_names=['negative', 'positive']))
        return accuracy_score(test_label_list, predictions)

    def pred_instance(self, data):
        pred = 0
        upper = 1
        for center, thre in zip(self.centers, self.thres):
            if self._distance(data, center) <= thre*upper:
                pred = 1
                break
        return pred


def snowman(viz=False):
    random.seed(1)
    np.random.seed(1)
    Path("models").mkdir(parents=True, exist_ok=True)
    # from guppy import hpy
    # h = hpy()
    # print(h.heap())
    xy = pd.read_csv("synthetic_snowman_clusters.csv")
    xy = xy[["x1", "x2", "y"]]

    xy = xy.iloc[::15]
    size = len(xy)
    print("total dataset size:", size)

    X = xy[["x1", "x2"]].values
    y = xy[["y"]].values

    print(X[:,0].shape)
    print(y.shape)

    if viz:
        f, (ax1) = plt.subplots(nrows=1, ncols=1,figsize=(8,8))
        sns.scatterplot(X[:,0],X[:,1],hue=y[:,0],ax=ax1);
        plt.show();


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


    "MCClassifier"
    
    start = timeit.default_timer()

    print("starrt mcc")

    clf = MCClassifier(metric="euclidean")
    target_precision_list = [0.9, 0.94]
    target_precision = 0.94
    centers, thres, _ = clf.train(train_data_list, train_label_list, stop_criterion=target_precision)
    print('MCClassifier training time: ', timeit.default_timer() - start)

    start = timeit.default_timer()
    for i in range(1):
    # for i in range(1000):
        accuracy = clf.test(test_data_list, test_label_list, print_result=0)
    print('MCClassifier test time: ', timeit.default_timer() - start)
    print("MCClassifier test accuracy:", accuracy)

    clf = MCClassifier(metric="euclidean")
    filename = 'models/mcc_snowman_mdl.sav'
    pickle.dump([clf, centers, thres], open(filename, 'wb'))


    "tslearnKNNClassifier (K=1)"

    model = tsLearnKNNClassifier()
    accuracy_score = model.run(train_data_list, train_label_list, test_data_list, test_label_list, \
        metric="euclidean")
    print("accuracy:", accuracy_score)


    "tslearnKNNClassifier (K=3)"
    
    model = tsLearnKNNClassifier()
    accuracy_score = model.run(train_data_list, train_label_list, test_data_list, test_label_list, \
        n_neighbors=3, metric="euclidean")
    print("accuracy:", accuracy_score)



    "sklearn library classifiers"
    for i in range(len(classifiers)):
        print(names[i])
        clf = classifiers[i]
        clf.fit(train_data_list, train_label_list)
        # save the model to disk
        filename = 'models/'+names[i]+'.sav'
        pickle.dump(clf, open(filename, 'wb'))
        start = timeit.default_timer()
        # for i in range(1000):
        accuracy_score = clf.score(test_data_list, test_label_list)
        print('Test Time: ', timeit.default_timer() - start, '\n\n')
        print("accuracy:", accuracy_score)


def snowman_outlier():
    viz = 0

    random.seed(1)
    np.random.seed(1)
    Path("models").mkdir(parents=True, exist_ok=True)
    # from guppy import hpy
    # h = hpy()
    # print(h.heap())

    xy = pd.read_csv("synthetic_snowman_clusters.csv")
    xy = xy[["x1", "x2", "y"]]
    xy = xy.iloc[::15]
    size = len(xy)

    # ============== add outlier
    xy.iloc[0] = [2, -4, 1]
    print("total dataset size:", size)

    X = xy[["x1", "x2"]].values
    y = xy[["y"]].values
    print(X[:,0].shape)
    print(y.shape)

    if viz:
        f, (ax1) = plt.subplots(nrows=1, ncols=1,figsize=(8,8))
        sns.scatterplot(X[:,0],X[:,1],hue=y[:,0],ax=ax1);
        plt.show();

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


    "MCClassifier"
    
    start = timeit.default_timer()

    clf = MCClassifier(metric="euclidean", seed_mode="costest")
    target_precision = 0.94
    centers, thres, _ = clf.train(train_data_list, train_label_list, stop_criterion=target_precision)
    print('MCClassifier training time: ', timeit.default_timer() - start)

    start = timeit.default_timer()
    # for i in range(1000):
    accuracy = clf.test(test_data_list, test_label_list, print_result=0)
    print('MCClassifier test time: ', timeit.default_timer() - start)
    print("MCClassifier test accuracy:", accuracy)

    clf = MCClassifier(metric="euclidean")
    filename = 'models/mcc_snowman_outlier_mdl.sav'
    pickle.dump([clf, centers, thres], open(filename, 'wb'))


    # "tslearnKNNClassifier (K=1)"

    # model = tsLearnKNNClassifier()
    # accuracy_score = model.run(train_data_list, train_label_list, test_data_list, test_label_list, \
    #     metric="euclidean")
    # print("accuracy:", accuracy_score)


    # "tslearnKNNClassifier (K=3)"
    
    # model = tsLearnKNNClassifier()
    # accuracy_score = model.run(train_data_list, train_label_list, test_data_list, test_label_list, \
    #     n_neighbors=3, metric="euclidean")
    # print("accuracy:", accuracy_score)

    exit()


    "sklearn library classifiers"
    for i in range(len(classifiers)):
        print(names[i])
        clf = classifiers[i]
        clf.fit(train_data_list, train_label_list)
        # save the model to disk
        filename = 'models/'+names[i]+'.sav'
        pickle.dump(clf, open(filename, 'wb'))
        start = timeit.default_timer()
        # for i in range(1000):
        accuracy_score = clf.score(test_data_list, test_label_list)
        print('Test Time: ', timeit.default_timer() - start, '\n\n')
        print("accuracy:", accuracy_score)


def load_mcc_model():
    xy = pd.read_csv("synthetic_snowman_clusters.csv")
    xy = xy[["x1", "x2", "y"]]
    xy = xy.iloc[::15]
    xy.iloc[0] = [2, -4, 1]
    X = xy[["x1", "x2"]].values
    y = xy[["y"]].values

    # filename = 'models/mcc_snowman_mdl.sav'
    filename = 'models/mcc_snowman_outlier_mdl.sav'
    clf, centers, thres = pickle.load(open(filename, 'rb'))
    for i in thres:
        print(i)

    figure, axes = plt.subplots()
    sns.scatterplot(X[:,0],X[:,1],hue=y[:,0],ax=axes)
    for i in range(len(thres)):
        draw_circle = plt.Circle((centers[i][0], centers[i][1]), thres[i], alpha=0.1, fc='yellow')
        axes.add_artist(draw_circle)
        plt.scatter(centers[i][0], centers[i][1], marker='^', c='k')
    plt.xlim((-5,5))
    plt.ylim((-6,6))
    plt.title('centers and thresholds')
    plt.show()


def trace_datasets():
    """
    in file datastruct.py use "from myDBA import performDBA"

    """
    from sklearn.model_selection import train_test_split
    from tslearn.datasets import CachedDatasets
    from tslearn.preprocessing import TimeSeriesScalerMeanVariance, \
        TimeSeriesResampler
    
    random.seed(0)
    np.random.seed(0)

    X_train, y_train, X_test, y_test = CachedDatasets().load_dataset("Trace")
    print(X_train.shape)
    print(X_test.shape)
    X_train = np.vstack((X_train, X_test))
    y_train = np.concatenate((y_train, y_test))
    # X_train = X_train[y_train < 3]  # Keep first 2 classes
    # X_test = X_test[y_test < 3]  # Keep first 2 classes

    # ----------------------------------------------------------------------
    #   MinMaxScaler
    # ----------------------------------------------------------------------
    scaler = MinMaxScaler()
    X_train = X_train.squeeze()
    X_train = X_train.T
    scaler.fit(X_train)  # shape: (timeseries_length, num_instances)
    X_train = scaler.transform(X_train)
    X_train = X_train.T
    X_train = np.expand_dims(X_train, axis=-1)
    X_train = TimeSeriesResampler(sz=40).fit_transform(X_train)


    print(X_test.shape)
    print(X_train.shape)

    X_train, X_test, y_train, y_test = train_test_split(X_train, y_train, \
        test_size=0.3, random_state=42)

    # scaler = MinMaxScaler()
    # X_test = X_test.squeeze()
    # X_test = X_test.T
    # scaler.fit(X_test)
    # X_test = scaler.transform(X_test)
    # X_test = X_test.T
    # X_test = np.expand_dims(X_test, axis=-1)
    # X_test = TimeSeriesResampler(sz=40).fit_transform(X_test)

    X_train_1 = X_train[y_train==1]
    X_train_2 = X_train[y_train==2]
    X_train_3 = X_train[y_train==3]
    X_train_4 = X_train[y_train==4]
    X_train_1 = X_train_1.squeeze()
    X_train_2 = X_train_2.squeeze()
    X_train_3 = X_train_3.squeeze()
    X_train_4 = X_train_4.squeeze()
    print(X_train_1.shape)
    print(X_train_2.shape)
    print(X_train_3.shape)
    print(X_train_4.shape)

    X_test_1 = X_test[y_test==1]
    X_test_2 = X_test[y_test==2]
    X_test_3 = X_test[y_test==3]
    X_test_4 = X_test[y_test==4]
    X_test_1 = X_test_1.squeeze()
    X_test_2 = X_test_2.squeeze()
    X_test_3 = X_test_3.squeeze()
    X_test_4 = X_test_4.squeeze()
    print(X_test_1.shape)
    print(X_test_2.shape)
    print(X_test_3.shape)
    print(X_test_4.shape)


    plt.subplot(3, 3, 1)
    for i in range(len(X_train_3)):
        plt.plot(X_train_3[i].ravel(), "k-", alpha=.2)
    for i in range(len(X_train_2)):
        plt.plot(X_train_2[i].ravel(), "k-", alpha=.2)
    plt.subplot(3, 3, 2)
    for i in range(len(X_train_1)):
        plt.plot(X_train_1[i].ravel(), "k-", alpha=.2)
    for i in range(len(X_train_4)):
        plt.plot(X_train_4[i].ravel(), "k-", alpha=.2)
    plt.subplot(3, 3, 3)
    for i in range(len(X_test_3)):
        plt.plot(X_test_3[i].ravel(), "k-", alpha=.2)
    for i in range(len(X_test_2)):
        plt.plot(X_test_2[i].ravel(), "k-", alpha=.2)
    plt.subplot(3, 3, 4)
    for i in range(len(X_test_1)):
        plt.plot(X_test_1[i].ravel(), "k-", alpha=.2)
    for i in range(len(X_test_4)):
        plt.plot(X_test_4[i].ravel(), "k-", alpha=.2)
    plt.show()
    

    train_data_list = []
    train_label_list = []
    for i in range(len(X_train_1)):
        train_data_list.append(X_train_1[i])
        train_label_list.append(0)
    for i in range(len(X_train_4)):
        train_data_list.append(X_train_4[i])
        train_label_list.append(0)
    for i in range(len(X_train_2)):
        train_data_list.append(X_train_2[i])
        train_label_list.append(1)
    for i in range(len(X_train_3)):
        train_data_list.append(X_train_3[i])
        train_label_list.append(1)


    test_data_list = []
    test_label_list = []
    for i in range(len(X_test_1)):
        test_data_list.append(X_test_1[i])
        test_label_list.append(0)
    for i in range(len(X_test_4)):
        test_data_list.append(X_test_4[i])
        test_label_list.append(0)
    for i in range(len(X_test_2)):
        test_data_list.append(X_test_2[i])
        test_label_list.append(1)
    for i in range(len(X_test_3)):
        test_data_list.append(X_test_3[i])
        test_label_list.append(1)

    print("\ntraining sample..")
    print(train_data_list[0])
    print(train_data_list[0].shape)



    "MCClassifier"
    start = timeit.default_timer()
    clf = MCClassifier(metric="dtw")
    target_precision = 0.90
    centers, thres, _ = clf.train(train_data_list, train_label_list, stop_criterion=target_precision)
    print(centers)
    print(thres)
    print('MCClassifier training time: ', timeit.default_timer() - start)

    start = timeit.default_timer()
    for i in range(100):
        accuracy = clf.test(test_data_list, test_label_list, print_result=0)
    print('MCClassifier test time: ', timeit.default_timer() - start)
    print("MCClassifier test accuracy:", accuracy)

    clf = MCClassifier(metric="dtw")
    filename = 'models/mcc_model.sav'
    pickle.dump([clf, centers, thres], open(filename, 'wb'))

    plt.subplot(3, 3, 5)
    colors = ["r","b","g","o","y"]
    for i in range(len(centers)):
        plt.plot(centers[i], color=colors[i], alpha=1)
    plt.show()


    "tslearnKNNClassifier (K=1)"

    model = tsLearnKNNClassifier()
    accuracy_score = model.run(train_data_list, train_label_list, test_data_list, test_label_list, \
        metric="dtw")
    print("accuracy:", accuracy_score)


    "tslearnKNNClassifier (K=3)"
    
    model = tsLearnKNNClassifier()
    accuracy_score = model.run(train_data_list, train_label_list, test_data_list, test_label_list, \
        n_neighbors=3, metric="dtw")
    print("accuracy:", accuracy_score)

    exit()


def trace_datasets_ndim():
    from sklearn.model_selection import train_test_split
    from tslearn.datasets import CachedDatasets
    from tslearn.preprocessing import TimeSeriesScalerMeanVariance, \
        TimeSeriesResampler
    
    random.seed(0)
    np.random.seed(0)

    X_train, y_train, X_test, y_test = CachedDatasets().load_dataset("Trace")
    print(X_train.shape)
    print(X_test.shape)
    X_train = np.vstack((X_train, X_test))
    y_train = np.concatenate((y_train, y_test))
    # X_train = X_train[y_train < 3]  # Keep first 2 classes
    # X_test = X_test[y_test < 3]  # Keep first 2 classes

    # ----------------------------------------------------------------------
    #   MinMaxScaler
    # ----------------------------------------------------------------------
    scaler = MinMaxScaler()
    X_train = X_train.squeeze()
    X_train = X_train.T
    scaler.fit(X_train)  # shape: (timeseries_length, num_instances)
    X_train = scaler.transform(X_train)
    X_train = X_train.T
    X_train = np.expand_dims(X_train, axis=-1)
    X_train = TimeSeriesResampler(sz=40).fit_transform(X_train)


    print(X_test.shape)
    print(X_train.shape)

    X_train, X_test, y_train, y_test = train_test_split(X_train, y_train, \
        test_size=0.3, random_state=42)

    # # scaler = MinMaxScaler()
    # X_test = X_test.squeeze()
    # X_test = X_test.T
    # scaler.fit(X_test)
    # X_test = scaler.transform(X_test)
    # X_test = X_test.T
    # X_test = np.expand_dims(X_test, axis=-1)
    # X_test = TimeSeriesResampler(sz=40).fit_transform(X_test)

    X_train_1 = X_train[y_train==1]
    X_train_2 = X_train[y_train==2]
    X_train_3 = X_train[y_train==3]
    X_train_4 = X_train[y_train==4]
    X_train_1 = X_train_1.squeeze()
    X_train_2 = X_train_2.squeeze()
    X_train_3 = X_train_3.squeeze()
    X_train_4 = X_train_4.squeeze()
    print(X_train_1.shape)
    print(X_train_2.shape)
    print(X_train_3.shape)
    print(X_train_4.shape)

    X_test_1 = X_test[y_test==1]
    X_test_2 = X_test[y_test==2]
    X_test_3 = X_test[y_test==3]
    X_test_4 = X_test[y_test==4]
    X_test_1 = X_test_1.squeeze()
    X_test_2 = X_test_2.squeeze()
    X_test_3 = X_test_3.squeeze()
    X_test_4 = X_test_4.squeeze()
    print(X_test_1.shape)
    print(X_test_2.shape)
    print(X_test_3.shape)
    print(X_test_4.shape)

    # plt.subplot(3, 3, 1)
    # for i in range(len(X_train_3)):
    #     plt.plot(X_train_3[i].ravel(), "k-", alpha=.2)
    # for i in range(len(X_train_2)):
    #     plt.plot(X_train_2[i].ravel(), "k-", alpha=.2)
    # plt.subplot(3, 3, 2)
    # for i in range(len(X_train_1)):
    #     plt.plot(X_train_1[i].ravel(), "k-", alpha=.2)
    # for i in range(len(X_train_4)):
    #     plt.plot(X_train_4[i].ravel(), "k-", alpha=.2)

    # plt.subplot(3, 3, 3)
    # for i in range(len(X_test_3)):
    #     plt.plot(X_test_3[i].ravel(), "k-", alpha=.2)
    # for i in range(len(X_test_2)):
    #     plt.plot(X_test_2[i].ravel(), "k-", alpha=.2)
    # plt.subplot(3, 3, 4)
    # for i in range(len(X_test_1)):
    #     plt.plot(X_test_1[i].ravel(), "k-", alpha=.2)
    # for i in range(len(X_test_4)):
    #     plt.plot(X_test_4[i].ravel(), "k-", alpha=.2)

    # plt.show()
    
    train_data_list = []
    train_label_list = []

    for i in range(len(X_train_1)):
        train_data_list.append(np.hstack((X_train_1[i].reshape(-1,1), X_train_1[i].reshape(-1,1)/2)))
        train_label_list.append(0)
    for i in range(len(X_train_4)):
        train_data_list.append(np.hstack((X_train_4[i].reshape(-1,1), X_train_4[i].reshape(-1,1)/2)))
        train_label_list.append(0)

    for i in range(len(X_train_2)):
        train_data_list.append(np.hstack((X_train_2[i].reshape(-1,1), X_train_2[i].reshape(-1,1)/2)))
        train_label_list.append(1)
    for i in range(len(X_train_3)):
        train_data_list.append(np.hstack((X_train_3[i].reshape(-1,1), X_train_3[i].reshape(-1,1)/2)))
        train_label_list.append(1)

    test_data_list = []
    test_label_list = []

    for i in range(len(X_test_1)):
        test_data_list.append(np.hstack((X_train_1[i].reshape(-1,1), X_train_1[i].reshape(-1,1)/2)))
        test_label_list.append(0)
    for i in range(len(X_test_4)):
        test_data_list.append(np.hstack((X_train_4[i].reshape(-1,1), X_train_4[i].reshape(-1,1)/2)))
        test_label_list.append(0)

    for i in range(len(X_test_2)):
        test_data_list.append(np.hstack((X_train_2[i].reshape(-1,1), X_train_2[i].reshape(-1,1)/2)))
        test_label_list.append(1)
    for i in range(len(X_test_3)):
        test_data_list.append(np.hstack((X_train_3[i].reshape(-1,1), X_train_3[i].reshape(-1,1)/2)))
        test_label_list.append(1)

    print("\ntraining sample")
    print(train_data_list[0])
    print(train_data_list[0].shape)
    print(len(train_data_list[0].shape))

    # exit()

    "MCClassifier"
    start = timeit.default_timer()
    clf = MCClassifier(metric="dtw")
    target_precision = 0.90
    centers, thres, _ = clf.train(train_data_list, train_label_list, stop_criterion=target_precision)
    print(centers)
    print(thres)
    print('MCClassifier training time: ', timeit.default_timer() - start)

    plt.subplot(3, 3, 5)
    colors = ["r","b","g","o","y"]
    for i in range(len(centers)):
        plt.plot(centers[i], color=colors[i], alpha=1)
    plt.show()

    start = timeit.default_timer()
    for i in range(100):
        accuracy = clf.test(test_data_list, test_label_list, print_result=0)
    print('MCClassifier test time: ', timeit.default_timer() - start)
    print("MCClassifier test accuracy:", accuracy)

    clf = MCClassifier(metric="dtw")
    filename = 'models/mcc_model.sav'
    pickle.dump([clf, centers, thres], open(filename, 'wb'))

    plt.subplot(3, 3, 5)
    colors = ["r","b","g","o","y"]
    for i in range(len(centers)):
        plt.plot(centers[i], color=colors[i], alpha=1)
    plt.show()



def ecg_dataset():
    random.seed(1)
    np.random.seed(1)

    train_data_list, train_label_list, test_data_list, test_label_list = pickle.load(\
        open("data/ecg_train_test_x_y.pkl", 'rb'))

    print(train_data_list[0])
    print(train_data_list[0].shape)
    print(len(train_data_list[0].shape))

    "MCClassifier"
    start = timeit.default_timer()
    clf = MCClassifier(metric="dtw", test_data_list=test_data_list, test_label_list=test_label_list)
    target_precision = 0.93
    centers, thres, _ = clf.train(train_data_list, train_label_list, stop_criterion=target_precision)
    print(thres)
    print('MCClassifier training time: ', timeit.default_timer() - start)

    start = timeit.default_timer()
    accuracy = clf.test(test_data_list, test_label_list)
    print('MCClassifier test time: ', timeit.default_timer() - start)
    print("MCClassifier test accuracy:", accuracy)


    "tslearnKNNClassifier (K=1)"
    model = tsLearnKNNClassifier()
    accuracy_score = model.run(train_data_list, train_label_list, test_data_list, test_label_list, \
        metric="dtw")
    print("accuracy:", accuracy_score)


    "tslearnKNNClassifier (K=3)"
    model = tsLearnKNNClassifier()
    accuracy_score = model.run(train_data_list, train_label_list, test_data_list, test_label_list, \
        n_neighbors=3, metric="dtw")
    print("accuracy:", accuracy_score)



if __name__ == '__main__':
    Path("models").mkdir(parents=True, exist_ok=True)
    # # load_mcc_model()
    # ecg_dataset()

    snowman()
    trace_datasets()
    # snowman_outlier()
    # trace_datasets_ndim()
    

