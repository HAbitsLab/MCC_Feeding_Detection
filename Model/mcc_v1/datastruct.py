import numpy as np
from collections.abc import Sequence
from myDBA import performDBA as performDBA_1d
from myDBA_ndim import performDBA as performDBA_ndim
from cdtw import dtw
import timeit


class Cluster(Sequence):

    def __init__(self, index, center, metric):
        self.index = index
        self.center = center  # numpy array
        self.instances = []
        self.pos_instances = []
        self.pos_dist_list = []
        self.neg_dist_list = []
        self.boundary = 0
        self.cost = 0
        self.metric = metric

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

    def _averaging_euclidean(self, pos_feature):
        self.center = np.mean(pos_feature, axis = 0)
        return self.center

    def _averaging_dba(self, pos_feature):
        if pos_feature.size == 0:
            print("warning: no positive sample in this cluster")
            return []
        else:
            # start = timeit.default_timer()
            if len(pos_feature.shape) == 3:
                self.center = performDBA_ndim(pos_feature, n_iterations=20)  # n_iterations <= 5 does not work
            else:
                self.center = performDBA_1d(pos_feature, n_iterations=20)  # n_iterations <= 5 does not work
            # print('update center DBA Time: ', timeit.default_timer() - start)
            return self.center
        
    def add_instance(self, instance, distance):
        self.instances.append(instance)

        if instance.label == 1:
            self.pos_dist_list.append(distance)
            self.pos_instances.append(instance)
        else:
            self.neg_dist_list.append(distance)

    def update_center(self):
        pos_feature = []
        for ins in self.instances:
            if ins.label == 1:  # use only positive instances to update the center
                pos_feature.append(ins.features)
        pos_feature = np.array(pos_feature)

        if self.metric == "euclidean":
            self._averaging_euclidean(pos_feature)
        elif self.metric == 'dtw':
            self._averaging_dba(pos_feature)

        return self.center

    def update_center_density_insensitive(self):
        pos_feature = []
        for ins in self.instances:
            if ins.label == 1:  # use only positive instances to update the center
                pos_feature.append(ins.features)

        tmp_min_dist = float('inf')
        for this_feat in pos_feature:
            tmp_this_dist = 0
            for candidate_feat in pos_feature:
                cand_dist = self._distance(this_feat, candidate_feat)
                if cand_dist > tmp_this_dist:
                    tmp_this_dist = cand_dist
            if tmp_this_dist < tmp_min_dist:
                tmp_min_dist = tmp_this_dist
                self.center = this_feat

        return self.center

    # def update_density_insensitive_dtw(self):
    #     pos_feature = []
    #     for ins in self.instances:
    #         if ins.label == 1:  # use only positive instances to update the center
    #             pos_feature.append(ins.features)


    def calc_cost(self):        
        self.cost = 0 
        for i in self.pos_dist_list:
            for j in self.neg_dist_list:
                temp = i - j
                if temp > 0:
                    self.cost += temp
#                     self.cost += 1
#         return self.cost/len(self.pos_dist_list)
        return self.cost

    def potential_cost_increase(self, pos_dist_add=None, neg_dist_add=None):  
        old_cost = self.calc_cost()
        new_cost = 0
        for i in self.pos_dist_list + pos_dist_add:
            for j in self.neg_dist_list + neg_dist_add:
                temp = i - j
                if temp > 0:
                    new_cost += temp
#                     new_cost += 1
#         return new_cost/len(self.pos_dist_list + pos_dist_add) - old_cost
        return new_cost - old_cost
    
    def __getitem__(self, index):
        return self.instances[index]

    def __len__(self):
        return len(self.instances)


class Instance:
    
    def __init__(self, features, label):
        self.features = features
        self.label = int(label)
        self.cluster = []
        
        
def unittest():
    ins = Instance([0,0],[0])
    a = [ins]
    b = [ins]
    print(a)
    a[0].label = [1]
    print(a[0].label)
    print(b[0].label)


if __name__ == '__main__':
    unittest()

