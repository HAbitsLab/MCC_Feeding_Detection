package com.example.mainapp.ui.main;


import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonWriter;

import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.net.URI;

class Utils {

    public static JsonArray getJsonArrayFromFile(String filepath) {
        Gson gson = new Gson();
        JsonArray array = null;
        try {
            File file = new File(new URI(filepath));
            FileReader fileReader = new FileReader(file.getAbsoluteFile());
            JsonReader jsonReader = new JsonReader(fileReader);
            array = gson.fromJson(jsonReader, JsonArray.class);
        } catch (Exception e) {
            e.printStackTrace();
        }

        return array;
    }

    public static double getdoubleFromStr(String string) {
        return Double.parseDouble(string);
    }

    public static void writeJsonArrayFromFile(String filepath, JsonArray jsonElements) {

        Gson gson = new Gson();
        try {
           File file = new File(filepath);
           if (!file.exists()){
               file.createNewFile();
           }
            FileWriter fileWriter = new FileWriter(filepath);
            JsonWriter jsonWriter = new JsonWriter(fileWriter);
            gson.toJson(jsonElements, jsonWriter);
            jsonWriter.flush();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}

