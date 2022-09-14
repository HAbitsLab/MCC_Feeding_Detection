import random
import copy
import numpy as np
from matplotlib import pyplot as plt
from sklearn.preprocessing import MinMaxScaler
# from myDTW import dtw
# from tslearn.metrics import dtw, dtw_path
from cdtw import dtw

from datastruct import Instance, Cluster
        

def visualize_2d(X,y,algorithm="tsne",title="Data in 2D",figsize=(8,8)):
    import seaborn as sns
    from sklearn.manifold import TSNE
    from sklearn.decomposition import PCA
    if algorithm == "tsne":
        reducer = TSNE(n_components=2,random_state=47,n_iter=400,angle=0.6)
    elif algorithm == "pca":
        reducer = PCA(n_components=2,random_state=47)
    else:
        raise ValueError("Unsupported dimensionality reduction algorithm given.")
    if X.shape[1] > 2:
        X = reducer.fit_transform(X)
    else:
        if type(X) == pd.DataFrame:
            X = X.values
    f, (ax1) = plt.subplots(nrows=1, ncols=1,figsize=figsize)
    sns.scatterplot(X[:,0],X[:,1],hue=y,ax=ax1)
    ax1.set_title(title)
    plt.show()


def plt_snowman_points_in_one_cluster(instances, centers):
    import seaborn as sns
    data = []
    # cluster = []
    for ins in instances:
        data.append(ins.features)
        # cluster.append(ins.cluster)
    data = np.array(data)
    # cluster = np.array(cluster)
    
    circle1 = plt.Circle((0, 0), np.sqrt(5), color='y', alpha = 0.1)
    circle2 = plt.Circle((0, 3), np.sqrt(2), color='y', alpha = 0.1)

    f, (ax1) = plt.subplots(nrows=1, ncols=1,figsize=(5,7))
    ax1.add_patch(circle1)
    ax1.add_patch(circle2)
    # sns.scatterplot(data[:,0], data[:,1], hue=cluster, ax=ax1)
    sns.scatterplot(data[:,0], data[:,1], ax=ax1)

    # plt.scatter(data[:,0],data[:,1])
    plt.scatter(centers[:,0], centers[:,1], color="k")
    ax1.set_xlim((-3, 3))
    ax1.set_ylim((-3, 5))
    plt.show()


def plt_trace(instances, centers):
    for ins in instances:
        plt.plot(ins.features, "b-", alpha=.2)
    for i in range(len(centers)):
        plt.plot(centers[i], "r-", alpha=1)
    plt.show()


def plt_trace_clusters(clusters, centers_feat):
    for i in range(len(clusters)):
        plt.subplot(1, len(clusters), i+1)
        for j in range(len(clusters[i].instances)):
            plt.plot(clusters[i].instances[j].features, "r-", alpha=.2)
        plt.plot(centers_feat[i], "k-", alpha=1)
    plt.show()


class DiscrepancyClustering(object):
    """    
    """
    def __init__(self, instances, metric="euclidean", priority="recall", balance_towards_recall=1, \
        verbose=False):
        
        self.version = "v2"

        assert metric in ["euclidean", "dtw"]
        self.metric = metric
        self.priority = priority
        self.balance_towards_recall = balance_towards_recall
        self.verbose = verbose
        self.instances = instances
        self.num_instances = len(instances)
        self.pos_instances = []
        self.neg_instances = []
        self.num_pos_instances = 0
        self.num_neg_instances = 0

        self.clusters = []
        self.num_clusters = 0
        self.centers_feat = []  # list of array

        self.furthest_outlier_ind = -1

        for i, ins in enumerate(self.instances):
            if ins.label == 1:
                self.pos_instances.append(ins)
                self.num_pos_instances += 1
            else:
                self.neg_instances.append(ins)
                self.num_neg_instances += 1
        
        if self.verbose:
            print("total pos samples", self.num_pos_instances)
            print("total neg samples", self.num_neg_instances)


    def _reset_assign_record(self):
        # reset clustering record, could be optimized            
        # Note these are index in the list of all POSITIVE samples, not all samples
        self.pos_assigned_ind = []
        self.pos_unassigned_ind = []
        # Note these are index in the list of all NEGATIVE samples, not all samples
        self.neg_assigned_ind = []
        self.neg_unassigned_ind = []

        for i in range(len(self.pos_instances)):
            self.pos_unassigned_ind.append(i)
        
        for i in range(len(self.neg_instances)):
            self.neg_unassigned_ind.append(i)


    def _reset_instances(self):
        for ins in self.instances:
            ins.cluster = []
        

    def _create_distance_mat(self):
        # split the distance matrix into two parts: negative one and positive one
        # will be (k, N+1) array, for k pos instances and N centroids; last col is index in all instances
        pos_dist_mat = []  
        # will be (k, N+1) array, for k neg instances and N centroids; last col is index in all instances
        neg_dist_mat = []  
        
        for i, ins in enumerate(self.instances):
            row = []  # row as [distance1, distance2, ..., index]
            for j, cent in enumerate(self.centers_feat):
                row.append(self._distance(ins.features, cent))
            
            row.append(i)
            if ins.label == 1:
                pos_dist_mat.append(row)
            else:
                neg_dist_mat.append(row)
        
        pos_dist_mat = np.array(pos_dist_mat)
        neg_dist_mat = np.array(neg_dist_mat)
        
        return pos_dist_mat, neg_dist_mat

            
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


    def _assign_positives(self, pos_dist_mat, neg_dist_mat, plot=False):
        # for each center, find the minimum distance between this center and any negative sample
        neg_thres = [min(neg_dist_mat[:, i]) for i in range(self.num_clusters)]
        if self.verbose:
            print("neg_thres", neg_thres)

        # for each center, find the positives that are closer than any negative, for speedup       
        for i in range(self.num_clusters):
            index_in_pos = np.argwhere(pos_dist_mat[:, i] < neg_thres[i])
            # update index record            
            for n in index_in_pos:
                n = int(n)
                if n not in self.pos_assigned_ind:
                    self.pos_assigned_ind.append(n)
                if n in self.pos_unassigned_ind:
                    self.pos_unassigned_ind.remove(n)
                # update cluster record
                self.clusters[i].add_instance(self.pos_instances[n], float(pos_dist_mat[n, i]))
                # update instance record
                self.pos_instances[n].cluster.append(i)

        if plot == True:
            plt_snowman_points_in_one_cluster(self.clusters[0].instances, np.array([self.centers_feat[0]]))
            plt_snowman_points_in_one_cluster(self.clusters[1].instances, np.array([self.centers_feat[1]]))

        furthest_outlier_cost = 0
        furthest_outlier_ind = -1
        cluster_belong_list = []

        for i in self.pos_unassigned_ind:
            min_cost = float("inf")  # list of potential cost increase for each center

            for j in range(self.num_clusters):
                temp = neg_dist_mat[:, j]
                cost = self.clusters[j].potential_cost_increase([pos_dist_mat[i, j]], \
                    temp[temp < pos_dist_mat[i, j]].tolist())

                if cost < min_cost:
                    cluster_belong = j
                    min_cost = cost

            if min_cost > furthest_outlier_cost:
                furthest_outlier_cost = min_cost
                furthest_outlier_ind = i

            # # NOTE: in this for-loop, never change the list this for-loop is iterating in      
            # # self.pos_assigned_ind.append(i)  # self.pos_unassigned_ind.remove(i)

            # # TEST code for misclassification 
            # if cluster_belong == 0:
            #     if self.pos_instances[i].features[1] > 3:
            #         print("NOTE: !!!!")
            
            # # update cluster record; NOTE THAT assign new points in the air will cause dynamic cost_increase 
            # for samples, which may be not favorable 
            # self.clusters[cluster_belong].add_instance(self.pos_instances[i], pos_dist_mat[i, cluster_belong])

            # update instance record
            self.pos_instances[i].cluster.append(cluster_belong)
            # can be optimized, don't need cluster_belong_list
            cluster_belong_list.append(cluster_belong)

        # update cluster's instances after going through all of the unassigned samples
        for k, i in enumerate(self.pos_unassigned_ind):
            # can read cluster_belong from instance object attribute
            cluster_belong = cluster_belong_list[k]
            self.clusters[cluster_belong].add_instance(self.pos_instances[i], pos_dist_mat[i, cluster_belong])

        if self.verbose:
            print(len(self.clusters[0].instances))
            print(len(self.clusters[1].instances))

        return furthest_outlier_ind  #, neg_thres
    

    def _assign_false_positives(self, pos_dist_mat, neg_dist_mat):
        max_pos_dists = {}
        for i in range(self.num_clusters):
            max_pos_dists[i] = 0

        # this double-for-loop can be optimized in _assign_positives
        for i, ins in enumerate(self.pos_instances):
            for cluster_belong in ins.cluster:
                if pos_dist_mat[i, cluster_belong] > max_pos_dists[cluster_belong]:
                    max_pos_dists[cluster_belong] = pos_dist_mat[i, cluster_belong]

        if self.verbose:
            print("max_pos_dists", max_pos_dists)

        for i in range(self.num_clusters):
            max_pos_dist = max_pos_dists[i]
            index_in_neg = np.argwhere(neg_dist_mat[:, i] < max_pos_dist)
            # update index record            
            for n in index_in_neg:
                n = int(n)
                if n not in self.neg_assigned_ind:
                    self.neg_assigned_ind.append(n)
                if n in self.neg_unassigned_ind:
                    self.neg_unassigned_ind.remove(n)
                # update cluster record
                self.clusters[i].add_instance(self.neg_instances[n], float(neg_dist_mat[n, i]))
                # update instance record
                self.neg_instances[n].cluster.append(i)

            if self.verbose:
                print("cluster {} has {} positive samples".format(i, len(self.clusters[i].pos_dist_list)))
                print("cluster {} has {} negative samples".format(i, len(self.clusters[i].neg_dist_list)))

        precision = self.num_pos_instances/(self.num_pos_instances + len(self.neg_assigned_ind))
        if self.verbose:
            print("In total, there are {} false positives".format(len(self.neg_assigned_ind)))
            print("precision:", precision)

        # ======================== improvement: how to choose the threshold
        # max_pos_dists_list = [max_pos_dists[i] for i in range(self.num_clusters)]
        max_pos_dists_list = [max_pos_dists[i] for i in range(self.num_clusters)]

        return precision, max_pos_dists_list


    def _total_cost(self):
        cost_new = 0
        for i in range(self.num_clusters):
            # print(self.clusters[i].calc_cost())
            cost_new += self.clusters[i].calc_cost()
        return cost_new


    def _highest_cost_cluster_ind(self):
        highest_cost = 0
        cluster_ind = 0
        for i in range(self.num_clusters):
            cost = self.clusters[i].calc_cost()
            if cost > highest_cost:
                highest_cost = cost
                cluster_ind = i
        return cluster_ind


    def _random_pick_center(self, instances, num_add_center):
        centers = []
        rand_history = []
        while num_add_center > 0:
            if self.verbose:
                print("randomly pick one from {} positive instances".format(len(instances)))
            r = random.randint(0, len(instances)-1)
            if r not in rand_history:
                centers.append(instances[r].features)
                rand_history.append(r)
                num_add_center -= 1
        
        return centers    


    def _pick_one_outlier_center(self):
        return [self.pos_instances[self.furthest_outlier_ind].features]

       
    def init_centers(self, num_add_center=2):
        new_centers = self._random_pick_center(self.pos_instances, num_add_center)
        return new_centers
        

    def updated_centers(self, num_add_center=1, seed_mode="random"):
        i = self._highest_cost_cluster_ind()
        if self.verbose:
            print("In total {} clusters".format(len(self.clusters)))

        assert seed_mode in ["random", "costest"] 
        if seed_mode == "random":
            new_center = self._random_pick_center(self.clusters[i].pos_instances, num_add_center) # new_center: list
        else:
            new_center = self._pick_one_outlier_center()  # new_center: list
        
        self.centers_feat += new_center
        self.num_clusters += 1

        return self.centers_feat


    def cluster(self, new_centers): 
        """
        Parameters
        ------------
        a list of centers

        Return
        ------------
        a list of new centers

        """
        self.centers_feat = new_centers
        self.num_clusters = len(self.centers_feat)

        flag_init = 1
        cost_decr = float("inf")
        cost_old = float("inf")
        precision_old = 0
        precision_incr = 1
        thresholds = []

        while precision_incr > 0:  # cost_decr > 0:
            self.clusters = [Cluster(i, new_centers[i], metric=self.metric) for i in range(self.num_clusters)]
            self._reset_assign_record()
            self._reset_instances()

            # # ----------------------------------------------------------------------
            # #  update centers
            # # ----------------------------------------------------------------------
            # if flag_init:
            #     flag_init = 0  # for init round, skip update centers
            # # else:
            #     self.centers_feat = []
            #     for i in range(self.num_clusters):
            #         center = self.clusters[i].update_center_euclidean()
            #         print(center)
            #         self.centers_feat.append(center)
            
            # ----------------------------------------------------------------------
            #  assign pos instances based on cost increase using distance matrix
            # ----------------------------------------------------------------------        
            pos_dist_mat, neg_dist_mat = self._create_distance_mat()
            self.furthest_outlier_ind = self._assign_positives(pos_dist_mat, neg_dist_mat)
                    
            # ----------------------------------------------------------------------
            #  assign false pos instances based on threshold
            # ----------------------------------------------------------------------
            precision, thresholds = self._assign_false_positives(pos_dist_mat, neg_dist_mat)
            # plt_snowman_points_in_one_cluster(self.clusters[0].instances, np.array([self.centers_feat[0]]))
            # plt_snowman_points_in_one_cluster(self.clusters[1].instances, np.array([self.centers_feat[1]]))

            # ----------------------------------------------------------------------
            #  calc cost_new
            # ----------------------------------------------------------------------
            cost_new = self._total_cost()
            cost_decr = cost_old - cost_new
            cost_old = cost_new

            # ----------------------------------------------------------------------
            #  calc increase
            # ----------------------------------------------------------------------
            precision_incr = precision - precision_old
            precision_old = precision
            thresholds_old = thresholds

            if self.verbose:
                print("cost_old: ", cost_old)

            # ----------------------------------------------------------------------
            #  record old center and thresholds
            # ----------------------------------------------------------------------
            self.centers_feat_old = self.centers_feat

            # ----------------------------------------------------------------------
            #  calc new center
            # ----------------------------------------------------------------------
            empty_cluster_list = []
            for i in range(self.num_clusters):
                if self.metric == "euclidean" or self.metric == "dtw":

                    if self.version == "v1":
                        center = self.clusters[i].update_center()
                    elif self.version == "v2":
                        center = self.clusters[i].update_center_density_insensitive()
                    else:
                        print("version must be v1 or v2")
                        exit()

                    if len(center) == 0:  # if no pos instance in a cluster
                        empty_cluster_list.append(i)
                else:
                    print('metric must be either euclidean (default) or dtw.')
                    exit()
                # print("updating cluster {}".format(i))
            
            self.centers_feat = [self.clusters[i].center for i in range(self.num_clusters) \
                if i not in empty_cluster_list]
            self.num_clusters = self.num_clusters - len(empty_cluster_list)
            
            if self.verbose:
                print(self.centers_feat)

            # plt_trace_clusters(self.clusters, self.centers_feat)
        # print("num_clusters", self.num_clusters)
        # print(self.pos_instances[furthest_outlier_ind].features)

        # ----------------------------------------------------------------------
        #  calc threshold
        # ----------------------------------------------------------------------
        # adjust threshold to balance recall and precision

        return self.centers_feat_old, thresholds_old, precision_old
    

def snowman():
    import pandas as pd
    import timeit

    xy = pd.read_csv("synthetic_snowman_clusters.csv")
    xy = xy[["x1", "x2", "y"]]
    xy = xy.iloc[::30]
    # visualize_2d(xy[["x1", "x2"]].values, xy[["y"]].values.reshape(-1))
    
    instances = []
    for i in range(len(xy)):
        instances.append(Instance(xy[["x1", "x2"]].iloc[i].values, xy[["y"]].iloc[i].values[0]))

    start = timeit.default_timer()

    clustering = DiscrepancyClustering(instances)
    print("total instances", clustering.num_instances)

    init_centers = clustering.init_centers(2)
    centers, thresholds, precision = clustering.cluster(init_centers)
    print(precision)
    print(centers)
    print(thresholds)

    stop = timeit.default_timer()
    print('Time: ', stop - start)


def trace_datasets():    
    import timeit
    from tslearn.datasets import CachedDatasets
    from tslearn.preprocessing import TimeSeriesScalerMeanVariance, \
        TimeSeriesResampler
    
    np.random.seed(1)
    X_train, y_train, X_test, y_test = CachedDatasets().load_dataset("Trace")
    # X_train = X_train[y_train < 3]  # Keep first 2 classes
    # X_test = X_test[y_test < 3]  # Keep first 2 classes
    print(X_test.shape)
    print(X_train.shape)


    # ----------------------------------------------------------------------
    #   MinMaxScaler
    # ----------------------------------------------------------------------
    scaler = MinMaxScaler()
    X_train = X_train.squeeze()
    X_train = X_train.T
    print(X_train.shape)
    scaler.fit(X_train)
    X_train = scaler.transform(X_train)

    X_train = X_train.T
    X_train = np.expand_dims(X_train, axis=-1)
    print(X_train.shape)


    X_train = TimeSeriesResampler(sz=40).fit_transform(X_train)
    X_test = TimeSeriesResampler(sz=40).fit_transform(X_test)

    X_train_1 = X_train[y_train==1]
    X_train_2 = X_train[y_train==2]
    X_train_3 = X_train[y_train==3]
    X_train_4 = X_train[y_train==4]

    X_train_1 = X_train_1.squeeze()
    X_train_2 = X_train_2.squeeze()
    X_train_3 = X_train_3.squeeze()
    X_train_4 = X_train_4.squeeze()
    print(X_train_3.shape)

    # center = performDBA(X_train_3, n_iterations=10)
    # print(center)
    # print(len(X_train_3))
    # print(len(X_train_2))

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

    instances = []
    # pos samples
    for i in range(len(X_train_3)):
        instances.append(Instance(X_train_3[i], 1))
    for i in range(len(X_train_2)):
        instances.append(Instance(X_train_2[i], 1))
    # neg samples
    for i in range(len(X_train_1)):
        instances.append(Instance(X_train_1[i], 0))
    for i in range(len(X_train_4)):
        instances.append(Instance(X_train_4[i], 0))

    start = timeit.default_timer()

    clustering = DiscrepancyClustering(instances, metric="dtw")
    print("total instances", clustering.num_instances)

    init_centers = clustering.init_centers(2)
    centers1, thresholds, precision = clustering.cluster(init_centers)
    print(precision)
    print(thresholds)

    stop = timeit.default_timer()
    print('Time: ', stop - start)



    plt.subplot(3, 3, 4)
    plt.plot(centers1[0], "r-", alpha=1)
    plt.plot(centers1[1], "r-", alpha=1)
    plt.show()



    # inner_dist = []
    # for i in range(len(X_train_4)):
    #     for j in range(len(X_train_4)):
    #         inner_dist.append(dtw.distance(X_train_4[i], X_train_4[j]))
    # # print(inner_dist)
    # from scipy import stats
    # print(stats.describe(inner_dist))

    # inner_dist = []
    # for i in range(len(X_train_2)):
    #     for j in range(len(X_train_2)):
    #         inner_dist.append(dtw.distance(X_train_2[i], X_train_2[j]))
    # # print(inner_dist)
    # from scipy import stats
    # print(stats.describe(inner_dist))

    # inner_dist = []
    # for i in range(len(X_train_2)):
    #     for j in range(len(X_train_4)):
    #         inner_dist.append(dtw.distance(X_train_2[i], X_train_4[j]))
    # # print(inner_dist)
    # from scipy import stats
    # print(stats.describe(inner_dist))


    # plt.subplot(3, 3, 1)
    # for i in range(len(X_train_1)):
    #     plt.plot(X_train_1[i].ravel(), "k-", alpha=.2)
    # plt.subplot(3, 3, 2)
    # for i in range(len(X_train_2)):
    #     plt.plot(X_train_2[i].ravel(), "k-", alpha=.2)
    # plt.subplot(3, 3, 3)
    # for i in range(len(X_train_3)):
    #     plt.plot(X_train_3[i].ravel(), "k-", alpha=.2)
    # plt.subplot(3, 3, 4)
    # for i in range(len(X_train_4)):
    #     plt.plot(X_train_4[i].ravel(), "k-", alpha=.2)
    # plt.show()



if __name__ == '__main__':
    trace_datasets()
    # snowman()


