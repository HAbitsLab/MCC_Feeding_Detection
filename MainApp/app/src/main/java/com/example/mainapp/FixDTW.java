package com.example.mainapp;

import android.content.Context;
import android.util.Log;


import com.example.mainapp.ml.SModel;

import org.tensorflow.lite.DataType;
import org.tensorflow.lite.Interpreter;
import org.tensorflow.lite.support.tensorbuffer.TensorBuffer;

import java.io.IOException;
import java.util.Arrays;

public class FixDTW {

    public static double[] arrayMinus(double[] a, double[] b) {
        double[] re = new double[a.length];
        for (int i = 0; i < a.length && i < b.length; i++) {
            re[i] = a[i] - b[i];
        }
        return re;
    }

    public static double selfDot(double[] a) {
        double v = 0;
        for (double x : a) {
            v += x * x;
        }
        return v;
    }

    public static double calcDTW(double[][] from, double[][] to) {
        int l1 = from.length;
        int l2 = to.length;

        double[][] E = new double[l1][l2];
        E[0][0] = selfDot(arrayMinus(from[0], to[0]));
        for (int i = 1; i < l1; i++) {
            E[i][0] = E[i - 1][0] + selfDot(arrayMinus(from[i], to[0]));
        }

        for (int i = 1; i < l2; i++) {
            E[0][i] = E[0][i - 1] + selfDot(arrayMinus(from[0], to[i]));
        }

        for (int i = 1; i < l1; i++) {
            for (int j = 1; j < l2; j++) {
                double v = selfDot(arrayMinus(from[i], to[i]));
                double v1 = E[i - 1][j];
                double v2 = E[i - 1][j - 1];
                double v3 = E[i][j - 1];
                if (v1 <= v2 && v1 <= v3)
                    E[i][j] = v1 + v;
                else if (v2 <= v1 && v2 <= v3)
                    E[i][j] = v2 + v;
                else
                    E[i][j] = v3 + v;
            }
        }
        return Math.sqrt(E[l1 - 1][l2 - 1]);
    }

    /**
     * w is window size
     * for length == 3, w == 1, the point map calculated is given below
     * - - -    - -
     * - - - => - - -
     * - - -      - -
     * The point to calc is reduced from 9 to 7
     *
     * @param w window size. you can use formula 'w= from.length / 2' to calculate
     * @param from from array
     * @param to to array
     * @return dtw
     */
    public static double calcOptimizeDTW(int w, double[][] from, double[][] to) {


        int l1 = from.length;
        int l2 = to.length;


        double[][] E = new double[l1][l2];
        E[0][0] = selfDot(arrayMinus(from[0], to[0]));
        for (int i = 1; i < Math.min(1 + w, l1); i++) {
            E[i][0] = selfDot(arrayMinus(from[i], to[0]));
        }
        for (int j = 1; j < Math.min(1 + w, l2); j++) {
            E[0][j] = selfDot(arrayMinus(from[0], to[j]));
        }

        if (w + 1 < l2) {
            E[0][w + 1] = Double.MAX_VALUE;
        }

        if (w + 1 < l1) {
            E[w + 1][0] = Double.MAX_VALUE;
        }

        for (int i = 1; i < l1; i++) {
            for (int j = i; j < Math.min(l2, i + w + 1); j++) { // row
                double cost = selfDot(arrayMinus(from[i], to[j]));
                double v1 = E[i - 1][j];
                double v2 = E[i - 1][j - 1];
                double v3 = E[i][j - 1];
                E[i][j] = cost + Math.min(v1, Math.min(v2, v3));
            }
            for (int k = i + 1; k < Math.min(l1, i + w + 1); k ++) { // col
                double cost = selfDot(arrayMinus(from[k], to[i]));
                double v1 = E[k - 1][i];
                double v2 = E[k - 1][i - 1];
                double v3 = E[k][i - 1];
                E[k][i] = cost + Math.min(v1, Math.min(v2, v3));
            }
            if (i + w + 1 < l2) {
                E[i][i + w + 1] = Double.MAX_VALUE;
            }
            if (i + w + 1 < l1) {
                E[i + w + 1][i] = Double.MAX_VALUE;
            }
        }
        return Math.sqrt(E[l1 - 1][l2 - 1]);
    }

    public static double[] calcOptimizeMultiDTW(int w, double[][][] from, double[][] to) {
        double[] re = new double[from.length];
        for (int i = 0; i < from.length; i++) {
            re[i] = calcOptimizeDTW(w, from[i], to);
        }
        return re;
    }

    public static double[] calcMultiDTW(double[][][] from, double[][] to) {
        double[] re = new double[from.length];
        for (int i = 0; i < from.length; i++) {
            re[i] = calcDTW(from[i], to);
        }
        return re;
    }


    public static double calcNDDTW(int window, double[][] from, double[][] to) {
        int n = from[0].length;
        int m = to[0].length;

        window = Math.max(window, Math.abs(m - n));

        // use one pixel larger matrix to avoid null
        double[][] matrixOfDtw = new double[n + 1][m + 1];
        for (int i = 0; i < matrixOfDtw.length; i++) {
            Arrays.fill(matrixOfDtw[i], Double.MAX_VALUE);
        }

        // init from 0
        matrixOfDtw[0][0] = 0.0;

        for (int i = 1; i < n + 1; i++) {
            // loop window for initial value;
            for (int j = Math.max(1, i - window); j < Math.min(m, i + window) + 1; j++) {
                matrixOfDtw[i][j] = 0;
            }
        }

        for (int i = 1; i < n + 1; i++) {
            // loop window for initial value;
            for (int j = Math.max(1, i - window); j < Math.min(m, i + window) + 1; j++) {
                double[] calcVal = new double[from.length];
                for (int r = 0; r < calcVal.length; r++) {
                    calcVal[r] = from[r][i - 1] - to[r][j - 1];
                }

                double cost = selfDot(calcVal);
                matrixOfDtw[i][j] = cost + Math.min(matrixOfDtw[i - 1][j - 1], Math.min(matrixOfDtw[i - 1][j], matrixOfDtw[i][j - 1]));
            }
        }
        return matrixOfDtw[n][m];
    }

    public static double[] calcMultiNDDTW(int window, double[][][] from, double[][] to) {
        double[] re = new double[from.length];
        for (int i = 0; i < from.length; i++) {
            re[i] = calcNDDTW(window, from[i], to);
        }
        return re;
    }

    public static int[] calDTWModel(float[][][] from, Context context) {
        try {
            SModel model = SModel.newInstance(context);

            // Creates inputs for reference.
            org.tensorflow.lite.support.tensorbuffer.TensorBuffer inputFeature0 = org.tensorflow.lite.support.tensorbuffer.TensorBuffer.createFixedSize(new int[]{1, 132, 3}, DataType.FLOAT32);
            int[] result = new int[from.length];
            for (int i = 0; i < from.length; i ++) {
                float[][] chunk = from[i];
                float[] merge = new float[chunk.length * chunk[0].length];
                for (int x = 0; x < chunk.length; x ++) {
                    for (int y = 0; y < chunk[x].length; y ++) {
                        merge[x * chunk[x].length + y] = chunk[x][y];
                    }
                }
                inputFeature0.loadArray(merge);
                // Runs model inference and gets result.
                SModel.Outputs outputs = model.process(inputFeature0);
                TensorBuffer outputFeature0 = outputs.getOutputFeature0AsTensorBuffer();
                float val = outputFeature0.getFloatValue(0);
                result[i] = val > 0.5 ? 1 : 0;
            }

            // Releases model resources if no longer used.
            model.close();
            return result;
        } catch (IOException e) {
            // TODO Handle the exception
            return new int[]{};
        }
    }

    public static int[] calRFModel(double[][][] from) {
       double[][] input = Normalizer.extract_stats_features(from);
       int[] re = new int[input.length];
       for (int i = 0; i < input.length; i ++) {
           re[i] = RandomForestClassifier.predict(input[i]);
       }
       return re;
    }

    public static int[] calSVCModel(double[][][] from) {
        double[][] input = Normalizer.extract_stats_features(from);
        int[] re = new int[input.length];
        for (int i = 0; i < input.length; i ++) {
            re[i] = LinearSVC.doPredict(input[i]);
        }
        return re;
    }

    public static int[] calKNNModel(double[][][] from, double[][] X, int[] y) {
        double[][] input = Normalizer.extract_stats_features(from);
        int[] re = new int[input.length];
        for (int i = 0; i < input.length; i ++) {
            re[i] = KNeighborsClassifier.doPredict(input[i], X, y);
        }
        return re;
    }

    public static int[] calGSModel(double[][][] a) {
        double[][] input = Normalizer.extract_motion_features(a);
        int[] re = new int[input.length];
        for (int i = 0; i < input.length; i ++) {
            re[i] = GaussianModel.doPredict(input[i]);
        }
        return re;
    }


//
//    public static void main(String[] args) {
//        File f1 = new File("templates.json");
//        File f2 = new File("test.json");
//        Gson gson = new Gson();
//
//        try {
//            double[][][] a = gson.fromJson(new FileReader(f1), double[][][].class);
//            double[][] b = gson.fromJson(new FileReader(f2), double[][].class);
//
//            double[] re = calcMultiDTW(a, b);
//            System.out.println(new Gson().toJson(re));
//        } catch (FileNotFoundException e) {
//            e.printStackTrace();
//        }
//    }

}
