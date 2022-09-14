import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn import preprocessing
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import *
from numpy import *
import joblib

'''
Thomaz et al approach:
Predict feeding gesture based on 5 statistical festures from accelerometer signals.
Link: https://dl.acm.org/doi/10.1145/2750858.2807545

Model parameters:
RandomForestClassifier(bootstrap=False, max_depth=70, max_features='sqrt', n_estimators=200)
KNeighborsClassifier(n_neighbors=3)
SVC(C=5.0, degree=4, gamma='auto')

'''

class Model():
    def __init__(self, optimize):
        self.optimize = optimize
        self.clf_rdf = None
        self.clf_knn = None
        self.clf_svm = None

    def get_statistical_features(self, features):
        train_example_final = []
        for each in features:
            temp = preprocessing.normalize(each, norm='l2')
            M_T = mean(temp,axis=0)
            V_T = var(temp,axis=0)
            SK_T = stats.skew(temp,axis=0)
            K_T = stats.kurtosis(temp,axis=0)
            RMS_T = sqrt(mean(temp**2,axis=0))
            H_T = hstack((M_T,V_T))
            H_T = hstack((H_T,SK_T))
            H_T = hstack((H_T,K_T))
            H_T = hstack((H_T,RMS_T))
            train_example_final.append(H_T)
        return(np.array(train_example_final))

    def optimize_model(self, clf_rdf, clf_knn, clf_svm, features, targets):
        cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=1)

        # Random Forest Optimize
        # Number of trees in random forest
        n_estimators = [int(x) for x in np.linspace(start = 100, stop = 1000, num = 5)]
        # Maximum number of levels in tree
        max_depth = [int(x) for x in np.linspace(10, 110, num = 11)]
        max_depth.append(None)
        # Minimum number of samples required to split a node
        min_samples_split = [2, 5, 10]
        # Minimum number of samples required at each leaf node
        min_samples_leaf = [1, 2, 4]
        # Create the random grid
        random_grid_rdf = {'n_estimators': n_estimators,
                           'max_depth': max_depth,
                           'min_samples_split': min_samples_split,
                           'min_samples_leaf': min_samples_leaf}
        search = RandomizedSearchCV(clf_rdf, random_grid_rdf, n_iter=10, scoring='f1', n_jobs=-1, cv=cv, random_state=1)
        rdf_parameters = search.fit(features, targets).best_params_

        # K-nearest neighbors Optimize
        # Number of neighbors to use
        n_neighbors = [3,5]
        # Create the random grid
        random_grid_knn = {'n_neighbors': n_neighbors}
        search = RandomizedSearchCV(clf_knn, random_grid_knn, n_iter=10, scoring='f1', n_jobs=-1, cv=cv, random_state=1)
        knn_parameters = search.fit(features, targets).best_params_

        # SVM Optimize
        # Regularization parameter.
        C = [1.0, 3.0, 5.0]
        # Specifies the kernel type to be used in the algorithm
        kernel=['rbf','linear', 'poly','sigmoid']
        # Degree of the polynomial kernel function (‘poly’). Ignored by all other kernels.
        degree = [3, 4, 5]
        # Kernel coefficient for ‘rbf’, ‘poly’ and ‘sigmoid’.
        gamma = ['scale', 'auto']
        random_grid_svm = {'C': C,
                           'kernel': kernel,
                           'degree': degree,
                           'gamma': gamma}
        search = RandomizedSearchCV(clf_svm, random_grid_svm, n_iter=10, scoring='f1', n_jobs=-1, cv=cv, random_state=1)
        svm_parameters = search.fit(features, targets).best_params_
        return(rdf_parameters, knn_parameters, svm_parameters)

    def fit(self, features, targets):
        features = self.get_statistical_features(features)
        clf_rdf = RandomForestClassifier()
        clf_knn = KNeighborsClassifier()
        clf_svm = SVC()
        if(self.optimize):
            rdf_parameters, knn_parameters, svm_parameters = self.optimize_model(clf_rdf, clf_knn, clf_svm, features, targets)
            clf_rdf = RandomForestClassifier(**rdf_parameters)
            clf_knn = KNeighborsClassifier(**knn_parameters)
            clf_svm = SVC(**svm_parameters)
        clf_rdf.fit(features, targets)
        clf_knn.fit(features, targets)
        clf_svm.fit(features, targets)
        self.clf_rdf = clf_rdf
        self.clf_knn = clf_knn
        self.clf_svm = clf_svm

    def predict(self, features):
    	features = self.get_statistical_features(features)
    	pred_rdf = self.clf_rdf.predict(features)
    	pred_knn = self.clf_knn.predict(features)
    	pred_svm = self.clf_svm.predict(features)
    	return(pred_rdf, pred_knn, pred_svm)

    def save(self, dir_save):
    	joblib.dump(self.clf_rdf, dir_save + 'rdf.sav')
    	joblib.dump(self.clf_knn, dir_save + 'knn.sav')
    	joblib.dump(self.clf_svm, dir_save + 'svm.sav')