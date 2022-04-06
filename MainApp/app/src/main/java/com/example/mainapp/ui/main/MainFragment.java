package com.example.mainapp.ui.main;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Message;
import android.provider.Settings;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import com.android.king.fileselector.FileSelector;
import com.android.king.fileselector.FileSelectorActivity;
import com.example.mainapp.R;

import java.io.File;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadPoolExecutor;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.app.ActivityCompat;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.ViewModelProvider;

public class MainFragment extends Fragment implements View.OnClickListener {

    private static final String TAG = "MainFragment";
    private static final int file_type_temp = 0;
    private static final int file_type_test = 1;
    private static final int REQUEST_EXTERNAL_STORAGE = 1;
    private static final int REQUEST_CODE = 1024;
    private static String[] PERMISSIONS_STORAGE = {
            Manifest.permission.READ_EXTERNAL_STORAGE,
            Manifest.permission.WRITE_EXTERNAL_STORAGE};
    private MainViewModel mViewModel;
    private TextView tv_template, tv_test, tv_test_result, tv_test_resultNew,
            tv_test_resultNewOptimize, tv_test_resultNewND, tv_costTime, tv_costTimeNew,
            tv_costTimeNewOptimize, tv_costTimeNewND, tv_costTimeNewModel, tv_test_resultNewModel,
            tv_costTimeRfModel, tv_test_resultRfModel, tv_costTimeSVCModel, tv_test_resultSVCModel,
            tv_costTimeKNNModel, tv_test_resultKNNModel, tv_costTimeGSModel, tv_test_resultGSModel, tv_epoch_input;
    private Button btn_template, btn_test, btn_pred;
    private int file_type = 0;
    //templates.json
    private String tempfilePath = null;
    //tset.json
    private String testfilePath = null;
    //test_results.json
    private String test_result_dwt_path = "test_results_dwt.json";
    private String test_result_dwt_fix_path = "test_results_dwt_new.json";
    private String test_result_dwt_nd_path = "test_results_dwt_new_nd.json";
    private String test_result_dwt_optimize_path = "test_results_dwt_new_optimize.json";
    private String test_result_dwt_model_path = "test_results_dwt_model.json";
    private String test_result_dwt_rf_model_path = "rf_model_path.json";
    private String test_result_dwt_svc_model_path = "svm_model_path.json";
    private String test_result_dwt_knn_model_path = "knn_model_path.json";
    private String test_result_dwt_gs_model_path = "gaussian_model_path.json";
    private String data_path = "";
    private AlertDialog mAlertDialog = null;
    private long costTime;
    private ThreadPoolExecutor executor = (ThreadPoolExecutor) Executors.newFixedThreadPool(1);
    private boolean save = true;
    private Handler mHandler = new Handler() {
        @Override
        public void handleMessage(@NonNull Message msg) {
            if (mAlertDialog == null) {
                return;
            }
            if (msg.what == 1) {
                tv_test_result.setText("");
                mAlertDialog.show();
            } else if (msg.what == 0) {
                mAlertDialog.dismiss();
                if (!save) tv_test_result.setText("");
                if (save) tv_test_result.setText(data_path + File.separator + test_result_dwt_path);
                tv_costTime.setText("CostTime: " + costTime + " ms ");
            } else if (msg.what == 10001) {
                tv_costTimeNew.setText("");
                mAlertDialog.show();
            } else if (msg.what == 10088) {
                mAlertDialog.dismiss();
                if (!save) tv_test_resultNew.setText("");
                if (save)
                    tv_test_resultNew.setText(data_path + File.separator + test_result_dwt_fix_path);
                tv_costTimeNew.setText("CostTime: " + costTime + " ms ");
            } else if (msg.what == 20001) {
                tv_costTimeNewOptimize.setText("");
                mAlertDialog.show();
            } else if (msg.what == 20088) {
                mAlertDialog.dismiss();
                if (!save) tv_test_resultNewOptimize.setText("");
                if (save)
                    tv_test_resultNewOptimize.setText(data_path + File.separator + test_result_dwt_optimize_path);
                tv_costTimeNewOptimize.setText("CostTime: " + costTime + " ms ");
            } else if (msg.what == 30001) {
                tv_costTimeNewND.setText("");
                mAlertDialog.show();
            } else if (msg.what == 30088) {
                // test_result_dwt_nd_path
                mAlertDialog.dismiss();
                if (!save) tv_test_resultNewND.setText("");
                if (save)
                    tv_test_resultNewND.setText(data_path + File.separator + test_result_dwt_nd_path);
                tv_costTimeNewND.setText("CostTime: " + costTime + " ms ");
            } else if (msg.what == 40001) {
                tv_costTimeNewModel.setText("");
                mAlertDialog.show();
            } else if (msg.what == 40088) {
                // test_result_dwt_nd_path
                mAlertDialog.dismiss();
                if (!save) tv_test_resultNewModel.setText("");
                if (save)
                    tv_test_resultNewModel.setText(data_path + File.separator + test_result_dwt_model_path);
                tv_costTimeNewModel.setText("CostTime: " + costTime + " ms ");
            } else if (msg.what == 50001) {
                tv_costTimeRfModel.setText("");
                mAlertDialog.show();
            } else if (msg.what == 50088) {
                // test_result_dwt_nd_path
                mAlertDialog.dismiss();
                if (!save) tv_test_resultRfModel.setText("");
                if (save)
                    tv_test_resultRfModel.setText(data_path + File.separator + test_result_dwt_rf_model_path);
                tv_costTimeRfModel.setText("CostTime: " + costTime + " ms ");
            } else if (msg.what == 60001) {
                tv_costTimeSVCModel.setText("");
                mAlertDialog.show();
            } else if (msg.what == 60088) {
                // test_result_dwt_nd_path
                mAlertDialog.dismiss();
                if (!save) tv_test_resultSVCModel.setText("");
                if (save)
                    tv_test_resultSVCModel.setText(data_path + File.separator + test_result_dwt_svc_model_path);
                tv_costTimeSVCModel.setText("CostTime: " + costTime + " ms ");
            } else if (msg.what == 70001) {
                tv_costTimeKNNModel.setText("");
                mAlertDialog.show();
            } else if (msg.what == 70088) {
                // test_result_dwt_nd_path
                mAlertDialog.dismiss();
                if (!save) tv_test_resultKNNModel.setText("");
                if (save)
                    tv_test_resultKNNModel.setText(data_path + File.separator + test_result_dwt_knn_model_path);
                tv_costTimeKNNModel.setText("CostTime: " + costTime + " ms ");
            } else if (msg.what == 80001) {
                tv_costTimeGSModel.setText("");
                mAlertDialog.show();
            } else if (msg.what == 80088) {
                // test_result_dwt_nd_path
                mAlertDialog.dismiss();
                if (!save) tv_test_resultGSModel.setText("");
                if (save)
                    tv_test_resultGSModel.setText(data_path + File.separator + test_result_dwt_gs_model_path);
                tv_costTimeGSModel.setText("CostTime: " + costTime + " ms ");
            }
        }
    };

    public static MainFragment newInstance() {
        return new MainFragment();
    }

    public void showToast(String string) {
        Toast.makeText(getActivity(), string, Toast.LENGTH_SHORT).show();
    }

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        return inflater.inflate(R.layout.main_fragment, container, false);
    }

    @Override
    public void onActivityCreated(@Nullable Bundle savedInstanceState) {
        super.onActivityCreated(savedInstanceState);
        mViewModel = new ViewModelProvider(this).get(MainViewModel.class);
        mAlertDialog = new AlertDialog.Builder(getActivity())
                .setMessage(getString(R.string.waiting))
                .setCancelable(false)
                .create();
    }

    public void onRadioButtonClickedCompute() {
        save = false;
    }

    public void onRadioButtonClickedSave() {
        save = true;
    }

    @Override
    public void onViewCreated(@NonNull @org.jetbrains.annotations.NotNull View view, @Nullable @org.jetbrains.annotations.Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        view.findViewById(R.id.save_rtb).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                save = true;
            }
        });
        view.findViewById(R.id.compute_rtb).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                save = false;
            }
        });
        tv_template = view.findViewById(R.id.tv_tempfile);
        tv_test = view.findViewById(R.id.tv_testfile);
        tv_test_result = view.findViewById(R.id.tv_test_result);
        tv_costTime = view.findViewById(R.id.tv_costtime);

        btn_template = view.findViewById(R.id.btn_tempfile);
        btn_test = view.findViewById(R.id.btn_testfile);
        btn_pred = view.findViewById(R.id.btn_predicate);

        btn_template.setOnClickListener(this);
        btn_test.setOnClickListener(this);
        btn_pred.setOnClickListener(this);


        tv_test_resultNew = view.findViewById(R.id.tv_test_result_new);
        tv_test_resultNewOptimize = view.findViewById(R.id.tv_test_result_new_optimize);
        tv_costTimeNew = view.findViewById(R.id.tv_costtime_new);
        tv_costTimeNewOptimize = view.findViewById(R.id.tv_costtime_new_optimize);

        tv_costTimeNewND = view.findViewById(R.id.tv_costtime_new_nd);
        tv_test_resultNewND = view.findViewById(R.id.tv_test_result_new_nd);

        tv_costTimeNewModel = view.findViewById(R.id.tv_costtime_new_model);
        tv_test_resultNewModel = view.findViewById(R.id.tv_test_result_new_model);

        tv_costTimeRfModel = view.findViewById(R.id.tv_costtime_rf_model);
        tv_test_resultRfModel = view.findViewById(R.id.tv_test_result_rf_model);

        tv_costTimeSVCModel = view.findViewById(R.id.tv_costtime_svc_model);
        tv_test_resultSVCModel = view.findViewById(R.id.tv_test_result_svc_model);

        tv_costTimeKNNModel = view.findViewById(R.id.tv_costtime_knn_model);
        tv_test_resultKNNModel = view.findViewById(R.id.tv_test_result_knn_model);

        tv_costTimeGSModel = view.findViewById(R.id.tv_costtime_gs_model);
        tv_test_resultGSModel = view.findViewById(R.id.tv_test_result_gs_model);

        tv_epoch_input = view.findViewById(R.id.epoch_input);

        view.findViewById(R.id.btn_predicate_dtw).setOnClickListener(this);
        view.findViewById(R.id.btn_predicate_dtw_optimize).setOnClickListener(this);
        view.findViewById(R.id.btn_predicate_dtw_nd).setOnClickListener(this);
        view.findViewById(R.id.btn_predicate_dtw_model).setOnClickListener(this);
        view.findViewById(R.id.btn_predicate_rf_model).setOnClickListener(this);
        view.findViewById(R.id.btn_predicate_svc_model).setOnClickListener(this);
        view.findViewById(R.id.btn_predicate_knn_model).setOnClickListener(this);
        view.findViewById(R.id.btn_predicate_gs_model).setOnClickListener(this);
    }


    @Override
    public void onClick(View v) {
        int n = 1;
        try {
            n = Integer.parseInt(tv_epoch_input.getText().toString());
        } catch (Throwable ignored) {
            n = 1;
        }
        switch (v.getId()) {
            case R.id.btn_tempfile:
                file_type = file_type_temp;
                requestPermission();
                break;

            case R.id.btn_testfile:
                file_type = file_type_test;
                requestPermission();
                break;

            case R.id.btn_predicate:
//                if (TextUtils.isEmpty(tempfilePath) || TextUtils.isEmpty(testfilePath)) {
//                    showToast(getString(R.string.warn_no_json));
//                    return;
//                }
                doPredictaion(n);
                break;
            case R.id.btn_predicate_dtw:
//                if (TextUtils.isEmpty(tempfilePath) || TextUtils.isEmpty(testfilePath)) {
//                    showToast(getString(R.string.warn_no_json));
//                    return;
//                }
                doPredictionDTW(n);
                break;
            case R.id.btn_predicate_dtw_optimize:
//                if (TextUtils.isEmpty(tempfilePath) || TextUtils.isEmpty(testfilePath)) {
//                    showToast(getString(R.string.warn_no_json));
//                    return;
//                }
                doPredictionOptimizeDTW(n);
                break;
            case R.id.btn_predicate_dtw_nd:
//                if (TextUtils.isEmpty(tempfilePath) || TextUtils.isEmpty(testfilePath)) {
//                    showToast(getString(R.string.warn_no_json));
//                    return;
//                }
                doPredictionNDDTW(n);
                break;
            case R.id.btn_predicate_dtw_model:
//                if (TextUtils.isEmpty(testfilePath)) {
//                    showToast(getString(R.string.warn_no_json));
//                    return;
//                }
                doPredictionModel(n);
                break;
            case R.id.btn_predicate_rf_model:
//                if (TextUtils.isEmpty(testfilePath)) {
//                    showToast(getString(R.string.warn_no_json));
//                    return;
//                }
                doPredictionRfModel(n);
                break;
            case R.id.btn_predicate_svc_model:
//                if (TextUtils.isEmpty(testfilePath)) {
//                    showToast(getString(R.string.warn_no_json));
//                    return;
//                }
                doPredictionSVCModel(n);
                break;
            case R.id.btn_predicate_knn_model:
//                if (TextUtils.isEmpty(testfilePath)) {
//                    showToast(getString(R.string.warn_no_json));
//                    return;
//                }
                doPredictionKNNModel(n);
                break;
            case R.id.btn_predicate_gs_model:
//                if (TextUtils.isEmpty(testfilePath)) {
//                    showToast(getString(R.string.warn_no_json));
//                    return;
//                }
                doPredictionGSModel(n);
                break;
            default:
                break;
        }
    }

    private void doPredictionGSModel(int n) {
        executor.execute(new Runnable() {
            @Override
            public void run() {
                costTime = 0;
                mHandler.sendEmptyMessage(80001);
                String resultDTWJson = data_path + File.separator + test_result_dwt_gs_model_path;
                costTime += mViewModel.doPredictGSModel(
                        tempfilePath, testfilePath, resultDTWJson, getContext(), n, save
                );
                mHandler.sendEmptyMessage(80088);
            }
        });
    }

    private void doPredictionSVCModel(int n) {
        executor.execute(new Runnable() {
            @Override
            public void run() {
                costTime = 0;
                mHandler.sendEmptyMessage(60001);
                String resultDTWJson = data_path + File.separator + test_result_dwt_svc_model_path;
                costTime += mViewModel.doPredictSVCModel(
                        tempfilePath, testfilePath, resultDTWJson, getContext(), n, save
                );
                mHandler.sendEmptyMessage(60088);
            }
        });
    }

    private void doPredictionKNNModel(int n) {
        executor.execute(new Runnable() {
            @Override
            public void run() {
                costTime = 0;
                mHandler.sendEmptyMessage(70001);

                String resultDTWJson = data_path + File.separator + test_result_dwt_knn_model_path;
                costTime += mViewModel.doPredictKNNModel(
                        tempfilePath, testfilePath, resultDTWJson, getContext(), n, save
                );
                mHandler.sendEmptyMessage(70088);
            }
        });
    }

    private void doPredictionModel(int n) {
        executor.execute(new Runnable() {
            @Override
            public void run() {
                costTime = 0;
                mHandler.sendEmptyMessage(40001);
                String resultDTWJson = data_path + File.separator + test_result_dwt_model_path;
                costTime += mViewModel.doPredictModel(
                        tempfilePath, testfilePath, resultDTWJson, getContext(), n, save
                );
                mHandler.sendEmptyMessage(40088);
            }
        });
    }

    private void doPredictionRfModel(int n) {
        executor.execute(new Runnable() {
            @Override
            public void run() {
                costTime = 0;
                mHandler.sendEmptyMessage(50001);
                String resultDTWJson = data_path + File.separator + test_result_dwt_rf_model_path;
                costTime += mViewModel.doPredictRfModel(
                        tempfilePath, testfilePath, resultDTWJson, getContext(), n, save
                );
                mHandler.sendEmptyMessage(50088);
            }
        });
    }

    private void doPredictionDTW(int n) {
        executor.execute(new Runnable() {
            @Override
            public void run() {
                costTime = 0;
                mHandler.sendEmptyMessage(10001);
                String resultDTWJson = data_path + File.separator + test_result_dwt_fix_path;
                costTime += mViewModel.doPredictionDTW(
                        tempfilePath, testfilePath, resultDTWJson, n, save, getContext()
                );
                mHandler.sendEmptyMessage(10088);
            }
        });
    }

    private void doPredictionOptimizeDTW(int n) {
        executor.execute(new Runnable() {
            @Override
            public void run() {
                costTime = 0;
                mHandler.sendEmptyMessage(20001);
                String resultDTWJson = data_path + File.separator + test_result_dwt_optimize_path;
                costTime += mViewModel.doPredictionOptimizeDTW(
                        tempfilePath, testfilePath, resultDTWJson, n, save, getContext()
                );
                mHandler.sendEmptyMessage(20088);
            }
        });
    }

    private void doPredictionNDDTW(int n) {
        executor.execute(new Runnable() {
            @Override
            public void run() {
                costTime = 0;
                mHandler.sendEmptyMessage(30001);
                String resultDTWJson = data_path + File.separator + test_result_dwt_nd_path;
                costTime += mViewModel.doPredictionNDDTW(
                        tempfilePath, testfilePath, resultDTWJson, n, save, getContext()
                );
                mHandler.sendEmptyMessage(30088);
            }
        });
    }


    private void dopickFiles() {
        ArrayList<String> filters = new ArrayList<String>();
        filters.add(FileSelectorActivity.FILE_TYPE_DOC);//文档
        FileSelector.Builder builder = new FileSelector.Builder(getActivity());
        Intent intent = builder.setFileRoot("")//初始路径  init file root
                .setIsMultiple(false)//是否多选模式 whether is multiple select
                .setMaxCount(1)//限定文件选择数 max file count
                .setFilters(filters)//筛选文件类型  file filter
                .getIntent();
        startActivityForResult(intent, 100);
    }

    private void doPredictaion(int n) {
        executor.execute(new Runnable() {
            @Override
            public void run() {
                mHandler.sendEmptyMessage(1);
                costTime = 0;
                String resultDTWJson = data_path + File.separator + test_result_dwt_path;
                boolean inf = tempfilePath == null || testfilePath == null;
                mViewModel.initTempData(tempfilePath, getContext());
                mViewModel.initTestData(testfilePath, getContext());
                costTime += mViewModel.dodtw(resultDTWJson, inf ? Integer.MAX_VALUE : n, save, getContext());
                mHandler.sendEmptyMessage(0);
            }
        });

    }

    private String getFileByUri(String url) {
        Uri uri = Uri.parse(url);
        List<String> paths = uri.getPathSegments();
        return paths.get(paths.size() - 1);
    }

    private String getFileDir(String filepath) {
        File file = null;
        String filepathTemp = "";
        try {
            file = new File(new URI(filepath));
        } catch (URISyntaxException e) {
            e.printStackTrace();
        }
        if (file != null) {
            filepathTemp = file.getParentFile().getAbsolutePath();
        }
        return filepathTemp;
    }

    @Override
    public void onActivityResult(int requestCode, int resultCode, @Nullable @org.jetbrains.annotations.Nullable Intent data) {
        if (resultCode == Activity.RESULT_OK && requestCode == 100 && data != null) {
            ArrayList<String> pathList = data.getStringArrayListExtra(FileSelectorActivity.ACTIVITY_KEY_RESULT_PATHLIST);
            for (String path : pathList) {
                Log.i(TAG, path);

                if (file_type == file_type_temp) {
                    tempfilePath = path;
                    tv_template.setText(getFileByUri(tempfilePath));
                }

                if (file_type == file_type_test) {
                    testfilePath = path;
                    tv_test.setText(getFileByUri(testfilePath));
                }

                data_path = getFileDir(path);

                break;
            }
        }
        if (requestCode == REQUEST_CODE && Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            if (Environment.isExternalStorageManager()) {
                Log.d("权限判断--------》", "含有权限");
                dopickFiles();
            } else {
                Log.d("权限判断--------》", "获取权限失败");
            }
        }

    }

    private void requestPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            // 先判断有没有权限
            if (Environment.isExternalStorageManager()) {
                Log.d("权限判断--------》", "含有权限");
                dopickFiles();
            } else {
                Intent intent = new Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION);
                intent.setData(Uri.parse("package:" + getActivity().getPackageName()));
                startActivityForResult(intent, REQUEST_CODE);
            }
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            // 先判断有没有权限
            if (ActivityCompat.checkSelfPermission(getActivity(), Manifest.permission.READ_EXTERNAL_STORAGE) == PackageManager.PERMISSION_GRANTED &&
                    ActivityCompat.checkSelfPermission(getActivity(), Manifest.permission.WRITE_EXTERNAL_STORAGE) == PackageManager.PERMISSION_GRANTED) {
                Log.d("权限判断--------》", "含有权限");
                dopickFiles();
            } else {
                ActivityCompat.requestPermissions(getActivity(), new String[]{Manifest.permission.READ_EXTERNAL_STORAGE, Manifest.permission.WRITE_EXTERNAL_STORAGE}, REQUEST_CODE);
            }
        } else {
            Log.d("权限判断--------》", "含有权限");
        }
    }


    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQUEST_CODE) {
            if (ActivityCompat.checkSelfPermission(getActivity(), Manifest.permission.READ_EXTERNAL_STORAGE) == PackageManager.PERMISSION_GRANTED &&
                    ActivityCompat.checkSelfPermission(getActivity(), Manifest.permission.WRITE_EXTERNAL_STORAGE) == PackageManager.PERMISSION_GRANTED) {
                Log.d("权限判断--------》", "含有权限");
                dopickFiles();
            } else {
                Log.d("权限判断--------》", "获取权限失败");
            }
        }
    }

}