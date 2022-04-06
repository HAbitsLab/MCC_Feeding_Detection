package com.example.mainapp;

class GaussianModel {

    private double[] priors;
    private double[][] sigmas;
    private double[][] thetas;

    public GaussianModel(double[] priors, double[][] sigmas, double[][] thetas) {
        this.priors = priors;
        this.sigmas = sigmas;
        this.thetas = thetas;
    }

    public static int doPredict(double[] features) {

        // Parameters:
        double[] priors = {0.8333333333333334, 0.16666666666666666};
        double[][] sigmas = {{683.8945617099208, 0.018021427748145538, 51.58391357003878, 0.07448378145890895}, {349.02271991652054, 0.010888658018699798, 19.74984558552527, 0.0518309025252102}};
        double[][] thetas = {{33.434514313975114, 1.5099848093784938, 7.162744944016221, 0.3234115884115875}, {47.37109146564737, 1.4310938949098335, 8.265811248614122, 0.5726523476523472}};

        // Prediction:
        GaussianModel clf = new GaussianModel(priors, sigmas, thetas);
        int estimation = clf.predict(features);
        return estimation;
    }

    public int predict(double[] features) {
        double[] likelihoods = new double[this.sigmas.length];

        for (int i = 0, il = this.sigmas.length; i < il; i++) {
            double sum = 0.;
            for (int j = 0, jl = this.sigmas[0].length; j < jl; j++) {
                sum += Math.log(2. * Math.PI * this.sigmas[i][j]);
            }
            double nij = -0.5 * sum;
            sum = 0.;
            for (int j = 0, jl = this.sigmas[0].length; j < jl; j++) {
                sum += Math.pow(features[j] - this.thetas[i][j], 2.) / this.sigmas[i][j];
            }
            nij -= 0.5 * sum;
            likelihoods[i] = Math.log(this.priors[i]) + nij;
        }

        int classIdx = 0;
        for (int i = 0, l = likelihoods.length; i < l; i++) {
            classIdx = likelihoods[i] > likelihoods[classIdx] ? i : classIdx;
        }
        return classIdx;
    }
}