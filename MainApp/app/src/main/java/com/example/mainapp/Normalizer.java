package com.example.mainapp;

public class Normalizer {

    public static double[][] extract_stats_features(double[][][] input) {
        double[][] result = new double[input.length][];
        for (int e = 0; e < input.length; e++) {
            double[][] each = input[e];
            // normalize
            for (int i = 0; i < each.length; i++) {
                double sumVar = 0.0f;
                for (int j = 0; j < each[i].length; j++) {
                    sumVar += each[i][j] * each[i][j];
                }
                sumVar = (double) Math.sqrt(sumVar);
                for (int j = 0; j < each[i].length; j++) {
                    each[i][j] = each[i][j] / sumVar;
                }
            }
            double[] ht = new double[each[0].length * 5];
            double[] mt = new double[each[0].length];
            double[] vt = new double[each[0].length];
            double[] skt = new double[each[0].length];
            double[] kt = new double[each[0].length];
            double[] rmsT = new double[each[0].length];
            for (int i = 0; i < each[0].length; i++) {
                double m = 0.0f;
                double rms = 0.0f;
                for (int j = 0; j < each.length; j++) {
                    m += each[j][i];
                    rms += each[j][i] * each[j][i];
                }
                m /= each.length;
                mt[i] = m;
                rms /= each.length;
                rms = (double) Math.sqrt(rms);
                rmsT[i] = rms;

                double v = 0.0f;
                for (int j = 0; j < each.length; j++) {
                    v += (each[j][i] - m) * (each[j][i] - m);
                }
                v /= each.length;
                vt[i] = v;

                double skew = 0.0f;
                double skew_b = 0.0f;
                double skew_u = 0.0f;

                double k_b = 0.0f;
                double k_u = 0.0f;

                for (int j = 0; j < each.length; j++) {
                    skew_u += Math.pow((each[j][i] - m), 3);
                    skew_b += Math.pow((each[j][i] - m), 2);

                    k_u += Math.pow((each[j][i] - m), 4);
                    k_b += Math.pow((each[j][i] - m), 2);
                }
                skew_b = (double) Math.sqrt(Math.pow(skew_b / each.length, 3));
                skew_u = skew_u / each.length;
                skew = (double) ((Math.sqrt(each.length * (each.length - 1)) / (each.length - 2)) * (skew_u / skew_b));
                skt[i] = skew;

                double k = (double) ((k_u / each.length) / Math.pow(k_b / each.length, 2) - 3);

                kt[i] = k;
            }
            System.arraycopy(mt, 0, ht, 0, 3);
            System.arraycopy(vt, 0, ht, 3, 3);
            System.arraycopy(skt, 0, ht, 6, 3);
            System.arraycopy(kt, 0, ht, 9, 3);
            System.arraycopy(rmsT, 0, ht, 12, 3);
            result[e] = ht;
        }
        return result;
    }

    public static double[][] extract_motion_features(double[][][] input) {
        double[][] result = new double[input.length][4];
        for (int i = 0; i < input.length; i++) {
            double[][] sub = input[i];

            double sum012 = 0.0;
            double sum345 = 0.0;

            double sum5 = 0.0;

            double f4 = 0;
            for (int j = 0; j < sub.length; j++) {
                sum012 += Math.abs(sub[j][0]) + Math.abs(sub[j][1]) + Math.abs(sub[j][2]);
                sum345 += ((Math.abs(sub[j][3]) + Math.abs(sub[j][4]) + Math.abs(sub[j][5])) /
                        (Math.abs(sub[j][0]) + Math.abs(sub[j][1]) + Math.abs(sub[j][2])));

                if (Math.abs(sub[j][5]) > 10) {
                    f4 += 1;
                }
                sum5 += Math.abs(sub[j][5]);
            }

            double f1 = sum345 / 132.0;
            f4 = f4 / 132.0;
            double f2 = sum012 / 132.0;

            double m5 = sum5 * 1.0 / sub.length;
            double f3 = 0.0;
            for (int j = 0; j < sub.length; j++) {
                f3 += (Math.abs(Math.abs(sub[j][5]) - m5));
            }
            f3 = f3 / 132.0;

            result[i] = new double[]{f1, f2, f3, f4};
        }
        return result;
    }

}