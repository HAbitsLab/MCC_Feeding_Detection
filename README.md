# MCC_Feeding_Detection
Open source Android-based app and Python code for detecting feeding gesture from a template-based matching algorithm.
## Setup
  **Step1:** Download master branch of “MCC_Feeding_Detection” repository from HABits Lab GitHub  

  **Step2:** Open "MainApp" that is in the “MCC_Feeding_Detection” folder in Android Studio  

  **Step3:** Build APKs

    Build -> build bundles/APKs -> build APKs

  **Step4:** Pair phone and watch  

    4.1. On phone: settings -> enable Bluetooth 
    4.2. On phone: download Wear OS app from Google Play Store 
    4.3. On phone: Wear OS -> connect to watch 
    4.4. On watch: setup
    4.5. Follow all prompts on watch and phone until pairing complete

  **Step5:** Enable developer mode on phone + watch  

    Settings -> about -> [tap build 7x]  

  **Step6:** Enable ADB on phone  

    6.1. Settings -> developer -> enable ADB debugging + enable debugging via USB
    6.2. Wear OS app -> advanced settings -> enable Bluetooth debugging  

  **Step7:** Enable ADB on watch  

    Settings -> developer -> enable ADB debugging + debugging via Bluetooth  

  **Step8:** Upload APKs to phone and watch  

    8.1. Connect phone to computer via USB
    8.2. Open terminal
    8.2.1. Change directory to APK folder (same as folder opened in Android Studio, by default)
      8.2.2. Enter commands:
        8.2.2.1. adb devices  (starts ADB sever + returns phone ID and connection status)
          8.2.2.1.1. It may be necessary to authorize ADB on the phone by selecting ‘allow’ on a notification that sometimes appears on the phone screen following this command
        8.2.2.2. adb forward tcp:4444 localabstract:/adb-hub
        8.2.2.3. adb connect 127.0.0.1:4444
          8.2.2.3.1. It may be necessary to authorize ADB on the watch by selecting ‘allow’ on a notification that sometimes appears on the phone screen following this command
        8.2.2.4. adb install -s [PHONE ID] [Mobile APK Name]
          8.2.2.4.1. Phone ID can be copied from output of first command
        8.2.2.5. adb install -s 127.0.0.1:4444 [Wear APK Name]

  **Step9:** Upload template and test file, and then choose the model you want to test

