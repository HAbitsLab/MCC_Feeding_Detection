    package com.example.mainapp.ui.main;


import android.util.Log;

/**
 * 表示 [3][132] 一个记录点
 */
public class WatchPoint {
    private final String TAG = "WatchPoint";
    public static final int Sample_demain = 3;
    public static final int Sample_size = 132;
    private double[][] data;

    public WatchPoint() {
        data = new double[Sample_demain][Sample_size];
    }

    public void initData(double[] n1, double[] n2, double[] n3) {
        for (int i = 0; i < Sample_size; i++) {
            data[0][i] = n1[i];
            data[1][i] = n2[i];
            data[2][i] = n3[i];
        }
    }

    public double getDistanceByDTW(WatchPoint watchPoint) {
        DTWHelper dtwHelper = new DTWHelper(Sample_size);
        dtwHelper.setWatchPointB(watchPoint);
        dtwHelper.compute();
        double distance = dtwHelper.warpingDistance;
//        Log.d(TAG,"distance = " + distance);
        return distance;
    }

    private class DTWHelper {
        protected int[][] warpingPath;
        protected int n;
        protected int m;
        protected int K;

        protected double warpingDistance;

        public void setWatchPointB(WatchPoint watchPointB) {
            mWatchPointB = watchPointB;
        }

        private WatchPoint mWatchPointB;

        public DTWHelper(int samplesize) {
            n = samplesize;
            m = samplesize;
            K = 1;
            warpingPath = new int[n + m][2];    // max(n, m) <= K < n + m
            warpingDistance = 0.0;
        }

        public void compute() {
            double accumulatedDistance = 0.0;

            double[][] d = new double[n][m];    // local distances
            double[][] D = new double[n][m];    // global distances

            for (int i = 0; i < n; i++) {
                for (int j = 0; j < m; j++) {
                    d[i][j] = distanceBetween(i, j);
                }
            }

            D[0][0] = d[0][0];

            for (int i = 1; i < n; i++) {
                D[i][0] = d[i][0] + D[i - 1][0];
            }

            for (int j = 1; j < m; j++) {
                D[0][j] = d[0][j] + D[0][j - 1];
            }

            for (int i = 1; i < n; i++) {
                for (int j = 1; j < m; j++) {
                    accumulatedDistance = Math.min(Math.min(D[i - 1][j], D[i - 1][j - 1]), D[i][j - 1]);
                    accumulatedDistance += d[i][j];
                    D[i][j] = accumulatedDistance;
                }
            }
            accumulatedDistance = D[n - 1][m - 1];

            int i = n - 1;
            int j = m - 1;
            int minIndex = 1;

            warpingPath[K - 1][0] = i;
            warpingPath[K - 1][1] = j;

            while ((i + j) != 0) {
                if (i == 0) {
                    j -= 1;
                } else if (j == 0) {
                    i -= 1;
                } else {    // i != 0 && j != 0
                    double[] array = {D[i - 1][j], D[i][j - 1], D[i - 1][j - 1]};
                    minIndex = this.getIndexOfMinimum(array);

                    if (minIndex == 0) {
                        i -= 1;
                    } else if (minIndex == 1) {
                        j -= 1;
                    } else if (minIndex == 2) {
                        i -= 1;
                        j -= 1;
                    }
                } // end else
                K++;
                warpingPath[K - 1][0] = i;
                warpingPath[K - 1][1] = j;
            } // end while
            warpingDistance = accumulatedDistance / K;

            this.reversePath(warpingPath);
        }

        public void compute2(){
            double accumulatedDistance = 0.0;

            double[][] d = new double[n][m];    // local distances
            double[][] D = new double[n][m];    // global distances

            for (int i = 0; i < n; i++) {
                for (int j = 0; j < m; j++) {
                    d[i][j] = distanceBetween(i, j);
                }
            }

            D[0][0] = d[0][0];
            for(int i=0;i<n;i++){
                for(int j=0;j<m;j++){
                    //这里要对i,j进行判定，其实就是加入边界值的考虑
                    if(i>00&&j>0){
                        D[i][j]=minDist(D[i][j-1]+d[i][j],D[i-1][j]+d[i][j],D[i-1][j-1]+2*d[i][j]);
                    }
                    else if(i==0&&j>0){
                        D[i][j] = D[i][j-1]+d[i][j];
                    }
                    else if(i>0&&j==0){
                        D[i][j]= D[i-1][j]+d[i][j];
                    }else{
                        D[i][j]=0;
                    }

                }
            }
            warpingDistance = D[n-1][m-1];
        }

        public void compute3(){

            double[][] M = new double[m][n];
            double[][] Mc = new double[m][n];
            //距离矩阵
            for(int i=0;i<m;i++) {
                for(int j=0;j<n;j++) {
                    M[i][j] = distanceBetween(i, j);
                }
            }
            //距离矩阵输出测试
            for(int i=0;i<m;i++) {
                for(int j=0;j<n;j++) {
                    System.out.print(M[i][j]+"\t");
                }
                System.out.println();
            }
            System.out.println("----------------");
            //累积距离矩阵
            Mc[0][0] = M[0][0];
            for(int i=1;i<m;i++) {
                Mc[i][0] = Mc[i-1][0] + M[i][0];
            }
            for(int j=1;j<n;j++) {
                Mc[0][j] = Mc[0][j-1] + M[0][j];
            }
            for(int i=1;i<m;i++) {
                for(int j=1;j<n;j++) {
                    Mc[i][j] = Min(Mc[i-1][j],Mc[i][j-1],Mc[i-1][j-1])+M[i][j];
                }
            }
            //累积距离矩阵输出测试
            for(int i=0;i<m;i++) {
                for(int j=0;j<n;j++) {
                    System.out.print(Mc[i][j]+"\t");
                }
                System.out.println();
            }
            System.out.println("----------------");
            System.out.println(Mc[m-1][n-1]);
            warpingDistance = Mc[m-1][n-1];
        }

        public void compute4(){
            int inf = 9000;
            double[][] dtw = new double[m + 1][n + 1];

            dtw[0][0] = 0;
            for (int i = 1; i <m + 1; i++) {
                dtw[i][0] = inf;
            }
            for (int i = 1; i <m + 1; i++) {
                dtw[0][i] = inf;
            }

            for (int i = 1; i < m + 1; i++) {
                for (int j = 1; j < m + 1; j++) {
                    double cost = distanceBetween(i - 1, j - 1);
                    dtw[i][j] = cost + minimum(dtw[i - 1][j],      //match
                            dtw[i][j - 1],      //insertion
                            dtw[i - 1][j - 1]); //deletion
                }
            }
            warpingDistance = dtw[m][n];
        }
        /**
         * Changes the order of the warping path (increasing order)
         *
         * @param path the warping path in reverse order
         */
        protected void reversePath(int[][] path) {
            int[][] newPath = new int[K][2];
            for (int i = 0; i < K; i++) {
                for (int j = 0; j < 2; j++) {
                    newPath[i][j] = path[K - i - 1][j];
                }
            }
            warpingPath = newPath;
        }

        /**
         * Returns the warping distance
         *
         * @return
         */
        public double getDistance() {
            return warpingDistance;
        }

        /**
         * Computes a distance between two points
         *
         * @param p1 the point 1
         * @param p2 the point 2
         * @return the distance between two points
         */
        protected double distanceBetween(double p1, double p2) {
            return (p1 - p2) * (p1 - p2);
        }

        protected double distanceBetween(int inidex_A, int index_B) {
            double p1 = Math.pow(data[0][inidex_A] - mWatchPointB.data[0][index_B],2);
            double p2 = Math.pow(data[1][inidex_A] - mWatchPointB.data[1][index_B],2);
            double p3 = Math.pow(data[2][inidex_A] - mWatchPointB.data[2][index_B],2);
            return Math.sqrt(p1 + p2 + p3);
        }

        /**
         * Finds the index of the minimum element from the given array
         *
         * @param array the array containing numeric values
         * @return the min value among elements
         */
        protected int getIndexOfMinimum(double[] array) {
            int index = 0;
            double val = array[0];

            for (int i = 1; i < array.length; i++) {
                if (array[i] < val) {
                    val = array[i];
                    index = i;
                }
            }
            return index;
        }

        /**
         * Returns a string that displays the warping distance and path
         */
        public String toString() {
            String retVal = "Warping Distance: " + warpingDistance + "\n";
            retVal += "Warping Path: {";
            for (int i = 0; i < K; i++) {
                retVal += "(" + warpingPath[i][0] + ", " + warpingPath[i][1] + ")";
                retVal += (i == K - 1) ? "}" : ", ";

            }
            return retVal;
        }
        private double minDist(double dist1,double dist2,double dist3){
            return (dist1<dist2?(dist2<dist3?dist3:(dist1>dist3?dist3:dist1)):(dist2>dist3?dist3:dist2));

        }

        public  double Min(double a,double b,double c) {
            return (a<b?a:b)<c?(a<b?a:b):c;
        }

        ///Finds the lowest value and returns it
        private  double minimum(double i, double i1, double i2) {
            if (i < i1) {
                if (i < i2) {
                    return i;
                }
            } else if (i1 < i2) {
                return i1;
            }
            return i2;
        }
    }
}
