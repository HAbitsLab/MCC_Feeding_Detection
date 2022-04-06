package com.example.mainapp.ui.main;

import android.content.Context;
import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonWriter;

import com.example.mainapp.FixDTW;
import com.example.mainapp.KNNModel;
import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

import androidx.lifecycle.ViewModel;

public class MainViewModel extends ViewModel {
    private static final int MAX_Points_TEMPLATE = 100;
    private static final int MAX_Points_TEST = 1;
    private double[][] matrix = new double[3][132];
    private ArrayList<WatchPoint> mPoints_temp = new ArrayList<>(MAX_Points_TEMPLATE);
    private ArrayList<WatchPoint> mPoints_test = new ArrayList<>(MAX_Points_TEST);
    private ArrayList<ArrayList<Double>> mDistanceDTW = new ArrayList<>(MAX_Points_TEMPLATE);

    @Override
    protected void onCleared() {
        super.onCleared();
    }

    public void initTempData(String tempfilePath, Context context) {
        mPoints_temp.clear();
        JsonArray jsonArray = tempfilePath == null ? new Gson().fromJson(readFromfile("templates.json", context), JsonArray.class) : Utils.getJsonArrayFromFile(tempfilePath);
        Iterator<JsonElement> iterator = jsonArray.iterator();
        while (iterator.hasNext()) {
            JsonElement element = iterator.next();
            JsonArray jsonArray1 = element.getAsJsonArray();
            JsonArray jsonArray30 = jsonArray1.get(0).getAsJsonArray();
            JsonArray jsonArray31 = jsonArray1.get(1).getAsJsonArray();
            JsonArray jsonArray32 = jsonArray1.get(2).getAsJsonArray();

            WatchPoint watchPoint = new WatchPoint();
            for (int i = 0; i < WatchPoint.Sample_size; i++) {
                double n1 = Utils.getdoubleFromStr(jsonArray30.get(i).getAsString());
                matrix[0][i] = n1;
                double n2 = Utils.getdoubleFromStr(jsonArray31.get(i).getAsString());
                matrix[1][i] = n2;
                double n3 = Utils.getdoubleFromStr(jsonArray32.get(i).getAsString());
                matrix[2][i] = n3;
            }
            watchPoint.initData(matrix[0], matrix[1], matrix[2]);
            mPoints_temp.add(watchPoint);

        }
    }

    // test.json
    public void initTestData(String testfilePath, Context context) {
        mPoints_test.clear();
        JsonArray jsonArray = testfilePath == null ? new Gson().fromJson(readFromfile("test.json", context), JsonArray.class) : Utils.getJsonArrayFromFile(testfilePath);
        JsonArray jsonArray30 = jsonArray.get(0).getAsJsonArray();
        JsonArray jsonArray31 = jsonArray.get(1).getAsJsonArray();
        JsonArray jsonArray32 = jsonArray.get(2).getAsJsonArray();

        WatchPoint watchPoint = new WatchPoint();
        for (int i = 0; i < 132; i++) {
            double n1 = Utils.getdoubleFromStr(jsonArray30.get(i).getAsString());
            matrix[0][i] = n1;
            double n2 = Utils.getdoubleFromStr(jsonArray31.get(i).getAsString());
            matrix[1][i] = n2;
            double n3 = Utils.getdoubleFromStr(jsonArray32.get(i).getAsString());
            matrix[2][i] = n3;
        }
        watchPoint.initData(matrix[0], matrix[1], matrix[2]);
        mPoints_test.add(watchPoint);
    }

    public long dodtw(String tsetDTWFile, int n, boolean save, Context context) {
        long costTime = 0;
        mDistanceDTW.clear();
        for (int i = 0; i < n; i++) {
            ArrayList<Double> dtw = new ArrayList<>();
            long startTime = System.currentTimeMillis();
            for (WatchPoint watchPointTemp : mPoints_temp) {
                for (WatchPoint watchPointTest : mPoints_test) {
                    double distanDTW = watchPointTemp.getDistanceByDTW(watchPointTest);
                    dtw.add(distanDTW);
                }
            }
            long endTime = System.currentTimeMillis();
            costTime += endTime - startTime;
            mDistanceDTW.add(dtw);
        }

        JsonArray jsonArray = new JsonArray();
        for (ArrayList<Double> dtw : mDistanceDTW) {
            JsonArray arr = new JsonArray();
            for (Double d : dtw) {
                arr.add(d);
            }
            jsonArray.add(arr);
        }
        if (save) Utils.writeJsonArrayFromFile(tsetDTWFile, jsonArray);
        return costTime;
    }

    public long doPredictionDTW(String tempfilePath, String testfilePath, String resultDTWJson, int n, boolean save, Context context) {
        Gson gson = new Gson();
        boolean isInc = tempfilePath == null || testfilePath == null;
        try {
            double[][][] a = gson.fromJson(isInc ? readFromfile("templates.json", context) : new JsonReader(new FileReader(new File(new URI(tempfilePath)))), double[][][].class);
            double[][] b = gson.fromJson(isInc ? readFromfile("test.json", context) : new JsonReader(new FileReader(new File(new URI(testfilePath)))), double[][].class);
            long cost = 0;
            List<double[]> re = new ArrayList<>();
            for (int i = 0; i < (isInc ? Long.MAX_VALUE : n); i++) {
                long st = System.currentTimeMillis();
                re.add(FixDTW.calcMultiDTW(a, b));
                long end = System.currentTimeMillis();
                cost += end - st;
                try {
                    Thread.sleep(660);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
            if (save) {
                PrintWriter writer = new PrintWriter(resultDTWJson);
                writer.println(new Gson().toJson(re).replaceAll(",", ",\n    ")
                        .replaceAll("\\[", "\\[\n    ")
                        .replaceAll("]", "    \n]"));
                writer.flush();
            }
            return cost;
        } catch (FileNotFoundException | URISyntaxException e) {
            e.printStackTrace();
        }
        return -1;
    }

    public long doPredictionOptimizeDTW(String tempfilePath, String testfilePath, String resultDTWJson, int n, boolean save, Context context) {
        Gson gson = new Gson();
        boolean isInc = tempfilePath == null || testfilePath == null;
        try {
            double[][][] a = gson.fromJson(isInc ? readFromfile("templates.json", context) : new JsonReader(new FileReader(new File(new URI(tempfilePath)))), double[][][].class);
            double[][] b = gson.fromJson(isInc ? readFromfile("test.json", context) : new JsonReader(new FileReader(new File(new URI(testfilePath)))), double[][].class);

            // todo ..... change if u want to try other window size, but for b = 3, only w=0,1,2(eq dtw) is meaningful
            int w = b.length / 2;
            w = Math.max(1, w);

            long cost = 0;
            List<double[]> re = new ArrayList<>();
            for (int i = 0; i < (isInc ? Long.MAX_VALUE : n); i++) {
                long st = System.currentTimeMillis();
                re.add(FixDTW.calcOptimizeMultiDTW(w, a, b));
                long end = System.currentTimeMillis();
                cost += end - st;

                try {
                    Thread.sleep(660);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
            if (save) {
                PrintWriter writer = new PrintWriter(resultDTWJson);
                writer.println(new Gson().toJson(re).replaceAll(",", ",\n    ")
                        .replaceAll("\\[", "\\[\n    ")
                        .replaceAll("]", "    \n]"));
                writer.flush();
            }
            return cost;
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (URISyntaxException e) {
            e.printStackTrace();
        }
        return -1;
    }

    public long doPredictionNDDTW(String tempfilePath, String testfilePath, String resultDTWJson, int n, boolean save, Context context) {
        Gson gson = new Gson();
        boolean isInc = tempfilePath == null || testfilePath == null;
        try {
            double[][][] a = gson.fromJson(isInc ? readFromfile("templates.json", context) : new JsonReader(new FileReader(new File(new URI(tempfilePath)))), double[][][].class);
            double[][] b = gson.fromJson(isInc ? readFromfile("test.json", context) : new JsonReader(new FileReader(new File(new URI(testfilePath)))), double[][].class);

            int w = 8;
            long cost = 0;
            List<double[]> re = new ArrayList<>();
            for (int i = 0; i < (isInc ? Long.MAX_VALUE : n); i++) {
                long st = System.currentTimeMillis();
                re.add(FixDTW.calcMultiNDDTW(w, a, b));
                long end = System.currentTimeMillis();
                cost += end - st;
                if (isInc) {
                    try {
                        Thread.sleep(660);
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                }
            }
            if (save) {
                PrintWriter writer = new PrintWriter(resultDTWJson);
                writer.println(new Gson().toJson(re).replaceAll(",", ",\n    ")
                        .replaceAll("\\[", "\\[\n    ")
                        .replaceAll("]", "    \n]"));
                writer.flush();
            }
            return cost;
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (URISyntaxException e) {
            e.printStackTrace();
        }
        return -1;
    }

    public long doPredictModel(String tempfilePath, String testfilePath, String resultDTWJson, Context context, int n, boolean save) {
        Gson gson = new Gson();

        try {
            float[][][] a = gson.fromJson(testfilePath == null ? readFromfile("test_cnnlstm.json", context) : new JsonReader(new FileReader(new File(new URI(testfilePath)))), float[][][].class);
            long st = System.currentTimeMillis();
            List<int[]> re = new ArrayList<>();
            for (int i = 0; i < (testfilePath == null ? Long.MAX_VALUE : n); i++) {
                re.add(FixDTW.calDTWModel(a, context));
                if (testfilePath == null) {
                    try {
                        Thread.sleep(660);
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                }
            }
            long end = System.currentTimeMillis();
            if (save) {
                PrintWriter writer = new PrintWriter(resultDTWJson);
                writer.println(new Gson().toJson(re).replaceAll(",", ",\n    ")
                        .replaceAll("\\[", "\\[\n    ")
                        .replaceAll("]", "    \n]"));
                writer.flush();
            }
            return end - st;
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (URISyntaxException e) {
            e.printStackTrace();
        }
        return -1;
    }


    public long doPredictRfModel(String tempfilePath, String testfilePath, String resultDTWJson, Context context, int n, boolean save) {
        Gson gson = new Gson();

        try {
            double[][][] a = gson.fromJson(testfilePath == null ? readFromfile("test_cnnlstm.json", context) : new JsonReader(new FileReader(new File(new URI(testfilePath)))), double[][][].class);
            long st = System.currentTimeMillis();
            List<int[]> re = new ArrayList<>();
            for (int i = 0; i < (testfilePath == null ? Long.MAX_VALUE : n); i++) {
                re.add(FixDTW.calRFModel(a));
                if (testfilePath == null) {
                    try {
                        Thread.sleep(660);
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                }
            }
            long end = System.currentTimeMillis();
            if (save) {
                PrintWriter writer = new PrintWriter(resultDTWJson);
                writer.println(new Gson().toJson(re).replaceAll(",", ",\n    ")
                        .replaceAll("\\[", "\\[\n    ")
                        .replaceAll("]", "    \n]"));
                writer.flush();
            }
            return end - st;
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (URISyntaxException e) {
            e.printStackTrace();
        }
        return -1;
    }

    public long doPredictSVCModel(String tempfilePath, String testfilePath, String resultDTWJson, Context context, int n, boolean save) {
        Gson gson = new Gson();

        try {
            double[][][] a = gson.fromJson(testfilePath == null ? readFromfile("test_cnnlstm.json", context) : new JsonReader(new FileReader(new File(new URI(testfilePath)))), double[][][].class);
            long st = System.currentTimeMillis();
            List<int[]> re = new ArrayList<>();
            for (int i = 0; i < (testfilePath == null ? Long.MAX_VALUE : n); i++) {
                re.add(FixDTW.calSVCModel(a));
                if (testfilePath == null) {
                    try {
                        Thread.sleep(660);
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                }
            }
            long end = System.currentTimeMillis();
            if (save) {
                PrintWriter writer = new PrintWriter(resultDTWJson);
                writer.println(new Gson().toJson(re).replaceAll(",", ",\n    ")
                        .replaceAll("\\[", "\\[\n    ")
                        .replaceAll("]", "    \n]"));
                writer.flush();
            }
            return end - st;
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (URISyntaxException e) {
            e.printStackTrace();
        }
        return -1;
    }

    public long doPredictKNNModel(String tempfilePath, String testfilePath, String resultDTWJson, Context context, int n, boolean save) {
        Gson gson = new Gson();

        try {
            KNNModel model = gson.fromJson(tempfilePath == null ? readFromfile("knn_model_template.json", context) : new JsonReader(new FileReader(new File(new URI(tempfilePath)))), KNNModel.class);
            double[][][] a = gson.fromJson(testfilePath == null ? readFromfile("x_train.json", context) : new JsonReader(new FileReader(new File(new URI(testfilePath)))), double[][][].class);
            long st = System.currentTimeMillis();
            List<int[]> re = new ArrayList<>();
            for (int i = 0; i < (testfilePath == null || tempfilePath == null ? Long.MAX_VALUE : n); i++) {
                re.add(FixDTW.calKNNModel(a, model.getX(), model.getY()));
                if (testfilePath == null || tempfilePath == null) {
                    try {
                        Thread.sleep(660);
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                }
            }
            long end = System.currentTimeMillis();
            if (save) {
                PrintWriter writer = new PrintWriter(resultDTWJson);
                writer.println(new Gson().toJson(re).replaceAll(",", ",\n    ")
                        .replaceAll("\\[", "\\[\n    ")
                        .replaceAll("]", "    \n]"));
                writer.flush();
            }
            return end - st;
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (URISyntaxException e) {
            e.printStackTrace();
        }
        return -1;
    }


    public long doPredictGSModel(String tempfilePath, String testfilePath, String resultDTWJson, Context context, int n, boolean save) {
        Gson gson = new Gson();

        try {
            double[][][] a = gson.fromJson(testfilePath == null ? readFromfile("x_train_raw.json", context) : new JsonReader(new FileReader(new File(new URI(testfilePath)))), double[][][].class);
            long st = System.currentTimeMillis();
            List<int[]> re = new ArrayList<>();
            for (int i = 0; i < (testfilePath == null ? Long.MAX_VALUE : n); i++) {
                re.add(FixDTW.calGSModel(a));
                if (testfilePath == null) {
                    try {
                        Thread.sleep(660);
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                }
            }
            long end = System.currentTimeMillis();
            if (save) {
                PrintWriter writer = new PrintWriter(resultDTWJson);
                writer.println(new Gson().toJson(re).replaceAll(",", ",\n    ")
                        .replaceAll("\\[", "\\[\n    ")
                        .replaceAll("]", "    \n]"));
                writer.flush();
            }
            return end - st;
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (URISyntaxException e) {
            e.printStackTrace();
        }
        return -1;
    }

    public JsonReader readFromfile(String fileName, Context context) {
        StringBuilder returnString = new StringBuilder();
        InputStream fIn = null;
        InputStreamReader isr = null;
        try {
            fIn = context.getResources().getAssets()
                    .open(fileName);
            isr = new InputStreamReader(fIn);
            return new JsonReader(isr);
//            String line = "";
//            while ((line = input.readLine()) != null) {
//                returnString.append(line);
//            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }
}