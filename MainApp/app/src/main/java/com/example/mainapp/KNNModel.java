package com.example.mainapp;

public class KNNModel {

    double[][] X;
    int[] y;

    public KNNModel(double[][] x, int[] y) {
        X = x;
        this.y = y;
    }

    public KNNModel() {
    }

    public double[][] getX() {
        return X;
    }

    public void setX(double[][] x) {
        X = x;
    }

    public int[] getY() {
        return y;
    }

    public void setY(int[] y) {
        this.y = y;
    }
}
