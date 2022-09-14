package com.mlBattery.test;

import androidx.appcompat.app.AppCompatActivity;

import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;

import android.content.Intent;
import android.content.IntentFilter;
import android.os.AsyncTask;
import android.os.BatteryManager;
import android.os.Bundle;
import android.os.Environment;
import android.os.PowerManager;
import android.os.SystemClock;
import android.util.Log;
import android.view.View;
import android.view.WindowManager;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.Spinner;
import android.widget.TextView;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class MainActivity extends AppCompatActivity implements AdapterView.OnItemSelectedListener, SensorEventListener {
    public PyObject pyobj;
    public IntentFilter ifilter;
    public Intent batteryStatus;
    public String modelName = "";
    public String dataset = "Clemson";
    public String batteryStart = "0";
    public String batteryEnd = "0";
    public Sensor accelerometer;
    public SensorManager accelerometerManager;
    public Sensor gyroscope;
    public SensorManager gyroscopeManager;
    private File storageData;
    private FileWriter fw;
    private TextView textview;
    private boolean isRunning = false;
    private PowerManager.WakeLock wakeLock;

    @Override
    public void onSensorChanged(SensorEvent event) {
        //Log.i("Sensor", event.sensor.getName());
        long time_ms = System.currentTimeMillis() + (event.timestamp - SystemClock.elapsedRealtimeNanos()) / 1000000L;
        float data1 = event.values[0];
        float data2 = event.values[1];
        float data3 = event.values[2];

    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {

    }

    @Override
    public void onPointerCaptureChanged(boolean hasCapture) {

    }

    @Override
    protected void onPause() {
        super.onPause();
        accelerometerManager.unregisterListener(this);
        gyroscopeManager.unregisterListener(this);
    }

    @Override
    protected void onResume() {
        super.onResume();
        accelerometerManager.registerListener(this, accelerometer, 2520);
        gyroscopeManager.registerListener(this, gyroscope, 2520);


    }




    @Override
    public void onItemSelected(AdapterView<?> parent, View view,
                               int pos, long id) {
        if(parent.getId() == R.id.spinner){
            modelName = parent.getItemAtPosition(pos).toString();
            Log.i("Spinner", modelName);
        }
        else{
            dataset = parent.getItemAtPosition(pos).toString();
            Log.i("dataset", dataset);
        }
    }

    @Override
    public void onNothingSelected(AdapterView<?> parent) {
        // Another interface callback
    }
    public String getBattery(){
        batteryStatus = this.registerReceiver(null, ifilter);
        int level = batteryStatus.getIntExtra(BatteryManager.EXTRA_LEVEL, -1);
        int scale = batteryStatus.getIntExtra(BatteryManager.EXTRA_SCALE, -1);
        float batteryPct = level * 100 / (float)scale;
        Log.i("battery level: ", Float.toString(batteryPct));
        return Float.toString(batteryPct);
    }

    private class PythonTask extends AsyncTask<String, Void, String> {

        @Override
        protected String doInBackground(String... params) {

            isRunning = true;
            //setSensor();
            batteryStart = getBattery();
            Python py = Python.getInstance();
            pyobj = py.getModule("run");
            PyObject obj = pyobj.callAttr(modelName, dataset);

            //disableSensor();
            return "finish";
        }

        @Override
        protected void onPostExecute(String result) {
            super.onPostExecute(result);
            // do something with result
            //wakeLock.release();
            batteryEnd = getBattery();
            Log.i("start: ", batteryStart);
            Log.i("end: ",batteryEnd);
            isRunning = false;
            textview.setText(batteryStart + "-" +batteryEnd);
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if(!Python.isStarted()){
            Python.start(new AndroidPlatform(this));
        }
        setContentView(R.layout.activity_main);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        Spinner spinner1 = (Spinner) findViewById(R.id.spinner);
        ArrayAdapter<CharSequence> adapter1 = ArrayAdapter.createFromResource(this,
                R.array.planets_array, android.R.layout.simple_spinner_item);
        adapter1.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinner1.setAdapter(adapter1);
        spinner1.setOnItemSelectedListener(this);

        Spinner spinner2 = (Spinner) findViewById(R.id.data);
        ArrayAdapter<CharSequence> adapter2 = ArrayAdapter.createFromResource(this,
                R.array.data_array, android.R.layout.simple_spinner_item);
        adapter2.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinner2.setAdapter(adapter2);
        spinner2.setOnItemSelectedListener(this);
        Button start = findViewById(R.id.start);

        textview = (TextView)findViewById(R.id.show);
        textview.setText("Wait for start");
        //initialize battery monitor

        ifilter = new IntentFilter(Intent.ACTION_BATTERY_CHANGED);

        PowerManager powerManager = (PowerManager) getSystemService(POWER_SERVICE);
        wakeLock = powerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK,
                "MyApp::MyWakelockTag");
        //wakeLock.acquire();
        start.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                //Run python

                textview.setText("Running");
                new PythonTask().execute();

            }
        });
        accelerometerManager = (SensorManager)getSystemService(this.SENSOR_SERVICE);
        accelerometer = accelerometerManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
        gyroscopeManager = (SensorManager)getSystemService(this.SENSOR_SERVICE);
        gyroscope = gyroscopeManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE);
        storageData = new File(this.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS).getAbsolutePath()+"/test.csv");




    }
}