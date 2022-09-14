import numpy as np
import pickle
from sklearn.metrics import classification_report
from sklearn.metrics import accuracy_score
from tslearn.neighbors import KNeighborsTimeSeriesClassifier
from scipy.spatial import distance
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import classification_report



class tsLearnKNNClassifier(object):
    """note that it does not accept varying length input"""
    def __init__(self):
        n_neighbors=1
        metric="dtw"
                
        print("\nKNN, K={}, (tslearn)".format(str(n_neighbors)))
        self.knn_clf = KNeighborsTimeSeriesClassifier(n_neighbors=n_neighbors, metric=metric)  #  metric="euclidean"
        

    def run(self, train_list, train_label_list, test_list, test_label_list, n_neighbors=1, metric="dtw"):
        super(tsLearnKNNClassifier, self).__init__()
                
        print("\nKNN, K={}, (tslearn)".format(str(n_neighbors)))
        knn_clf = KNeighborsTimeSeriesClassifier(n_neighbors=n_neighbors, metric=metric)  #  metric="euclidean"
        knn_clf.fit(train_list, train_label_list)

        filename = 'models/tsLearn'+str(n_neighbors)+'NNClassifier.sav'
        pickle.dump(knn_clf, open(filename, 'wb'))

        import timeit
        start = timeit.default_timer()
        # for i in range(1000):
        predicted_labels = knn_clf.predict(test_list)
        print('tsLearnKNNClassifier Test Time: ', timeit.default_timer() - start)

        return accuracy_score(test_label_list, predicted_labels)


    def train(self, train_list, train_label_list):
        super(tsLearnKNNClassifier, self).__init__()

        self.knn_clf.fit(train_list, train_label_list)


    def test(self, test_list):
        super(tsLearnKNNClassifier, self).__init__()

        predicted_labels = self.knn_clf.predict(test_list)
        return predicted_labels


class CusKNNClassifier(object):
    """docstring for Classifier"""
    def __init__(self, w):
        super(CusKNNClassifier, self).__init__()
        self.w = w

    def DTWDistance(self, s1, s2,w):
        DTW={}
        
        w = max(w, abs(len(s1)-len(s2)))
        
        for i in range(-1,len(s1)):
            for j in range(-1,len(s2)):
                DTW[(i, j)] = float('inf')
        DTW[(-1, -1)] = 0
      
        for i in range(len(s1)):
            for j in range(max(0, i-w), min(len(s2), i+w)):
                dist= (s1[i]-s2[j])**2
                DTW[(i, j)] = dist + min(DTW[(i-1, j)],DTW[(i, j-1)], DTW[(i-1, j-1)])
            
        return np.sqrt(DTW[len(s1)-1, len(s2)-1])

    def LB_Keogh(self, s1,s2,r):
        LB_sum=0
        for ind,i in enumerate(s1):
            
            lower_bound=min(s2[(ind-r if ind-r>=0 else 0):(ind+r)])
            upper_bound=max(s2[(ind-r if ind-r>=0 else 0):(ind+r)])
            
            if i>upper_bound:
                LB_sum=LB_sum+(i-upper_bound)**2
            elif i<lower_bound:
                LB_sum=LB_sum+(i-lower_bound)**2
        
        return sqrt(LB_sum)

    def knn(self, train, test):
        preds = []
        for ind, i in enumerate(test):
            min_dist = float('inf')
            closest_seq = []
            for j in train:
                if self.LB_Keogh(i, j, 5) < min_dist:
                    dist = self.DTWDistance(i, j, self.w)
                    if dist < min_dist:
                        min_dist = dist
                        closest_seq = j
            preds.append(closest_seq[-1])

        return preds

    def train(self, train_list, train_label_list):
        self.train = train_list
        self.train_label = train_label_list

    
    def test(self, test_list):
        return self.knn(self.train, self.train_label, test_list)


    def test_result(self, test_list, test_label_list):
        return classification_report(test[:, -1],\
            self.knn(self.train, self.train_label, test_list))


class skLearnKNNClassifier(object):
    """note that it does not accept varying length input"""
    def __init__(self):
        n_neighbors=1
        metric="dtw"
                
        print("\nKNN, K={}, (tslearn)".format(str(n_neighbors)))
        self.knn_clf = KNeighborsTimeSeriesClassifier(n_neighbors=n_neighbors, metric=metric)  #  metric="euclidean"
        

    def run(self, train_list, train_label_list, test_list, test_label_list, n_neighbors=1, metric="dtw"):
        super(tsLearnKNNClassifier, self).__init__()
                
        print("\nKNN, K={}, (tslearn)".format(str(n_neighbors)))
        knn_clf = KNeighborsTimeSeriesClassifier(n_neighbors=n_neighbors, metric=metric)  #  metric="euclidean"
        knn_clf.fit(train_list, train_label_list)

        filename = 'models/tsLearn'+str(n_neighbors)+'NNClassifier.sav'
        pickle.dump(knn_clf, open(filename, 'wb'))

        import timeit
        start = timeit.default_timer()
        for i in range(1000):
            predicted_labels = knn_clf.predict(test_list)
        print('tsLearnKNNClassifier Test Time: ', timeit.default_timer() - start)

        return accuracy_score(test_label_list, predicted_labels)


    def train(self, train_list, train_label_list):
        super(tsLearnKNNClassifier, self).__init__()

        self.knn_clf.fit(train_list, train_label_list)


    def test(self, test_list):
        super(tsLearnKNNClassifier, self).__init__()

        predicted_labels = self.knn_clf.predict(test_list)
        return predicted_labels


#custom metric
def DTW(a, b):   
    an = a.size
    bn = b.size
    pointwise_distance = distance.cdist(a.reshape(-1,1),b.reshape(-1,1))
    cumdist = np.matrix(np.ones((an+1,bn+1)) * np.inf)
    cumdist[0,0] = 0
    
    for ai in range(an):
        for bi in range(bn):
            minimum_cost = np.min([cumdist[ai, bi+1],
                                   cumdist[ai+1, bi],
                                   cumdist[ai, bi]])
            cumdist[ai+1, bi+1] = pointwise_distance[ai,bi] + minimum_cost

    return cumdist[an, bn]

if __name__ == '__main__':
        
    #toy dataset 
    X = np.random.random((100,10))
    y = np.random.randint(0,2, (100))
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)

    #train
    clf = KNeighborsClassifier(metric=DTW, n_neighbors=1)
    clf.fit(X_train, y_train)

    #evaluate
    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred))


