package com.example.mainapp;

import java.util.*;

class KNeighborsClassifier {

    private int nNeighbors;
    private int nTemplates;
    private int nClasses;
    private double power;
    private double[][] X;
    private int[] y;

    public KNeighborsClassifier(int nNeighbors, int nClasses, double power, double[][] X, int[] y) {
        this.nNeighbors = nNeighbors;
        this.nTemplates = y.length;
        this.nClasses = nClasses;
        this.power = power;
        this.X = X;
        this.y = y;
    }

    private static class Neighbor {
        Integer clazz;
        Double dist;

        public Neighbor(int clazz, double dist) {
            this.clazz = clazz;
            this.dist = dist;
        }
    }

    private static double compute(double[] temp, double[] cand, double q) {
        double dist = 0.;
        double diff;
        for (int i = 0, l = temp.length; i < l; i++) {
            diff = Math.abs(temp[i] - cand[i]);
            if (q == 1) {
                dist += diff;
            } else if (q == 2) {
                dist += diff * diff;
            } else if (q == Double.POSITIVE_INFINITY) {
                if (diff > dist) {
                    dist = diff;
                }
            } else {
                dist += Math.pow(diff, q);
            }
        }
        if (q == 1 || q == Double.POSITIVE_INFINITY) {
            return dist;
        } else if (q == 2) {
            return Math.sqrt(dist);
        } else {
            return Math.pow(dist, 1. / q);
        }
    }

    public int predict(double[] features) {
        int classIdx = 0;
        if (this.nNeighbors == 1) {
            double minDist = Double.POSITIVE_INFINITY;
            double curDist;
            for (int i = 0; i < this.nTemplates; i++) {
                curDist = KNeighborsClassifier.compute(this.X[i], features, this.power);
                if (curDist <= minDist) {
                    minDist = curDist;
                    classIdx = y[i];
                }
            }
        } else {
            int[] classes = new int[this.nClasses];
            ArrayList<Neighbor> dists = new ArrayList<Neighbor>();
            for (int i = 0; i < this.nTemplates; i++) {
                dists.add(new Neighbor(y[i], KNeighborsClassifier.compute(this.X[i], features, this.power)));
            }
            Collections.sort(dists, new Comparator<Neighbor>() {
                @Override
                public int compare(Neighbor n1, Neighbor n2) {
                    return n1.dist.compareTo(n2.dist);
                }
            });
            for (Neighbor neighbor : dists.subList(0, this.nNeighbors)) {
                classes[neighbor.clazz]++;
            }
            for (int i = 0; i < this.nClasses; i++) {
                classIdx = classes[i] > classes[classIdx] ? i : classIdx;
            }
        }
        return classIdx;
    }

    public static int doPredict(double[] features, double[][] X, int[] y) {
        // Parameters:
        // Prediction:
        KNeighborsClassifier clf = new KNeighborsClassifier(5, 2, 2, X, y);

        // Prediction:
        int estimation = clf.predict(features);
        return estimation;
    }

}