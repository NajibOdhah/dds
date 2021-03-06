# coding: utf-8

# Import all the things we need ---
#get_ipython().magic(u'matplotlib inline')
import os,random
#os.environ["KERAS_BACKEND"] = "theano"
os.environ["KERAS_BACKEND"] = "tensorflow"
#os.environ["THEANO_FLAGS"]  = "device=gpu%d"%(1)   #disabled because we do not have a hardware GPU
import numpy as np
from copy import deepcopy
#import theano as th
#import theano.tensor as T
from keras.utils import np_utils
from keras.models import load_model
import keras.models as models
from keras.layers.core import Reshape,Dense,Dropout,Activation,Flatten
from keras.layers.convolutional import Conv2D, MaxPooling2D, ZeroPadding2D
from keras.regularizers import *
from keras.optimizers import adam
from keras.optimizers import adagrad
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
#import seaborn as sns
import cPickle, random, sys, keras
from keras.utils import multi_gpu_model
from keras import backend as K
K.tensorflow_backend._get_available_gpus()
import tensorflow as tf


# Dataset setup
Xd = cPickle.load(open("../data/RML2016.10b_dict.dat", 'rb'))
snrs, mods = map(lambda j: sorted(list(set(map(lambda x: x[j], Xd.keys())))), [1, 0])
X = []
Y_snr = []
lbl = []
for snr in snrs:
    for mod in mods:
        X.append(Xd[(mod, snr)])
        for i in range(Xd[(mod, snr)].shape[0]):  lbl.append((mod, snr))
        Y_snr = Y_snr + [mod]*6000
X = np.vstack(X)
Y_snr = np.vstack(Y_snr)


def to_onehot(yy):
    yy1 = np.zeros([len(yy), max(yy) + 1])
    yy1[np.arange(len(yy)), yy] = 1
    return yy1


# Use only the train split
np.random.seed(2016)
n_examples = X.shape[0]
n_train_valid = n_examples // 2
train_valid_idx = np.random.choice(range(0, n_examples), size=n_train_valid, replace=False)
X_train_valid = X[train_valid_idx]
n_train = 3 * n_train_valid // 4
train_idx = np.random.choice(range(0, n_train_valid), size=n_train, replace=False)
X = X_train_valid[train_idx]
valid_idx = list(set(range(0, n_train_valid))-set(train_idx))
X_valid = X_train_valid[valid_idx]
Y_snr = to_onehot(map(lambda x: mods.index(lbl[x][0]), range(X.shape[0])))

print("shape of X", np.shape(X))
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
num_samples = 64
new_X = []
orig_model = load_model('../models/cldnn_ranker.h5')
for eva_iter in range(X.shape[0]//60000):
    snr_data = X[eva_iter*60000:(eva_iter+1)*60000]
    snr_out = Y_snr[eva_iter*60000:(eva_iter+1)*60000]
    snr_acc_list = []
    snr_data_copy = deepcopy(snr_data)
    for idx in range(X.shape[2]):
        snr_data = deepcopy(snr_data_copy)
        snr_data = snr_data.transpose((2, 1, 0))
        new_snr_data = np.append(snr_data[:idx], np.zeros((1, snr_data.shape[1], snr_data.shape[2])), axis=0)
        snr_data = np.append(new_snr_data, snr_data[idx+1:], axis=0)
        snr_data = snr_data.transpose((2, 1, 0))
        score = orig_model.evaluate(snr_data, snr_out, batch_size=60000, verbose=0)
        snr_acc_list.append((idx, score[1]))
    snr_acc_list.sort(key=lambda x: x[1])
    snr_acc_list = snr_acc_list[:num_samples]
    snr_acc_list.sort(key=lambda x: x[0]) 
    snr_idxs = [ele[0] for ele in snr_acc_list]
    snr_data = snr_data.transpose((2, 1, 0))
    snr_data = snr_data[snr_idxs]
    snr_data = snr_data.transpose((2, 1, 0))
    new_X = new_X + [snr_data]
    print(eva_iter)
X = np.vstack(new_X)
np.save('../ranker_samples/cldnn/cldnn_'+str(num_samples)+'.npy', X)
