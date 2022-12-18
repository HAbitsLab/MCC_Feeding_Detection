# MCC Intake Detection
An End-to-end Energy-efficient Approach for Intake Detection With Low Inference Time Using Wrist-worn Sensor
 
### Device requirement:
API version: 28 <br>
Memory Required: 600 MB <br>

### Instruction:
After installed, open the app on wristband and the selection droplist for model and data will be shown. After click on start, the training and predicting process will start running on backend and a text message "wait" will show up. <b>Do not exist the app while it is running</b> since Android system will stop the program from running on backend. 

### Process: 
For model 1,2,3,6: first run model training, then run model inference with 2 second interval<br>
For model 4: first run model 4 training, then run model 4 inference <b>without a 2 second wait</b><br>
For model 5: first run model 5 training, then run a combination of training and inference with 2 second interval.<br>
For model 7,8: run model inference with 2 second interval<br>
