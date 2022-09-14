from model_1.inference import model_inference_1
from model_1.train import model_train_1
from model_2.inference import model_inference_2
from model_2.train import model_train_2
from model_3.inference import model_inference_3
from model_3.train import model_train_3
from model_4.inference import model_inference_4
from model_4.train import model_train_4
from model_5.inference import model_inference_5
from model_5.train import model_train_5
from model_6.inference import model_inference_6
from model_6.train import model_train_6
from model_7.inference import model_inference_7
from model_8.inference import model_inference_8

def Training_1236(dataset):
    model_train_1(dataset)
    model_train_2(dataset)
    model_train_3(dataset)
    model_train_6(dataset)

def Training_4(dataset):
    model_train_4(dataset)

def Training_5(dataset):
    model_train_5(dataset)

def Training_6(dataset):
    model_train_6(dataset)

def Model_1(dataset):
    model_inference_1(dataset)

def Model_2(dataset):
    model_inference_2(dataset)

def Model_3(dataset):
    model_inference_3(dataset)

def Model_4(dataset):
    #model_train_4()
    model_inference_4(dataset)

def Model_5(dataset):
    #model_train_5()
    model_inference_5(dataset)

def Model_6(dataset):
    model_inference_6(dataset)

def Model_7(dataset):
    model_inference_7(dataset)

def Model_8(dataset):
    model_inference_8(dataset)