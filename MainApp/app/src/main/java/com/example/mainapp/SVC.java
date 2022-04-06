package com.example.mainapp;

class LinearSVC {

    private double[] coefficients;
    private double intercepts;

    public LinearSVC(double[] coefficients, double intercepts) {
        this.coefficients = coefficients;
        this.intercepts = intercepts;
    }

    public int predict(double[] features) {
        double prob = 0.;
        for (int i = 0, il = this.coefficients.length; i < il; i++) {
            prob += this.coefficients[i] * features[i];
        }
        if (prob + this.intercepts > 0) {
            return 1;
        }
        return 0;
    }

    public static int doPredict(double[] features) {
        // Parameters:
        double[] coefficients = {0.1711071795702636, 1.0087978287664772, 0.7989458680307607, 3.7833904603301214, 0.22810187010817312, 0.866352542710667, 0.49228314596502315, -0.12015610116361636, -0.01961423521083978, -0.3430711068443272, -0.05922281325046152, 0.05806420312446576, 2.3508393027496255, 0.4230582982935936, -0.673916541358886};
        double intercepts = -2.487613368217838;

        // Prediction:
        LinearSVC clf = new LinearSVC(coefficients, intercepts);
        int estimation = clf.predict(features);
        return estimation;
    }
}