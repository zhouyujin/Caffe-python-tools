import sys
sys.path.insert(0, '../../python/')

import caffe
import numpy as np
from sklearn.metrics import confusion_matrix
from kappa import kappa(y_true, y_pred, weights, allow_off_by_one)

caffe_root = '../../'
caffe.set_mode_gpu()

# network parameters:
deploy_name = 'ge_01v234_40r-2-40r-2-40r-2-40r-4-256rd0.5-256rd0.5'
network_name = deploy_name + '-wd0.0001-lr0.001_24K-lr0.0003'
iterations = '78000'
rotation = '180'

net = caffe.Classifier(model_file='deploy.' + deploy_name + '.prototxt',
                       pretrained_file='../../../data/models/' + network_name + '_iter_' + iterations + '.caffemodel',
                       )
transformer = caffe.io.Transformer({'data': net.blobs['data'].data.shape})
transformer.set_transpose('data', (2,0,1))
net.blobs['data'].reshape(1,1,512,512)

train_sm = "../../../data/train_g/train_g_" + rotation + "/"

if (sys.argv[1] == 'val'):
    f = open("../validation.g.csv")
    cnt = 7472
    print_file = open("validations_" + network_name + "_iter_" + iterations + "_" + rotation + ".csv", "w")
elif (sys.argv[1] == 'trainfull'):
    f = open("../train.original.csv")
    cnt = 27652
    print_file = open("trainfull_" + network_name + "_iter_" + iterations + "_" + rotation + ".csv", "w")
else:
    f = open("../train-5K.txt")
    cnt = 5531
    print_file = open("train_" + network_name + "_iter_" + iterations + "_" + rotation + ".csv", "w")

error = 0
preds = []
labels = []

def debug(labels, preds):
    print "processed ", len(preds), " / ", cnt, " images..."
    pred_cnt = [0] * 25
    for iter in range(len(preds)):
        pred_cnt[labels[iter] * 5 + preds[iter]] += 1
    for i in range(5):
        for j in range(5):
            print '%5d ' % pred_cnt[i * 5 + j], 
        print ""
    print "\nkappa = ", kappa(labels, preds, weights='quadratic')

processed = 0
for iter in range(cnt):
    if ((iter-1) % 100 == 0 and processed>0):
        debug(labels, preds)
    
    st = f.readline()
    name = st.split(' ')[0]
    label = int(st.split(' ')[1]) 
    
    processed += 1

    net.blobs['data'].data[...] = transformer.preprocess(
        'data', 
        caffe.io.load_image(train_sm + name, color=False))
    
    out = net.forward()
  
    ip2 = net.blobs['ip2'].data[0]
    x = ip2[0];
    
    pred = 0
    if (x < 0.506057):
        pred = 0
    elif x < 0.704131:
        pred = 1
    elif x < 0.834754:
        pred = 2
    elif x < 0.86702:
        pred = 3
    else:
        pred = 4
    
    preds.append(pred)
    labels.append(label)
    
    print_file.write(str(name) + "," + str(label) + "," + str(pred) + "," + str(x) + '\n')
    
    if (pred != label):
        error += 1

debug(labels, preds)
print "total = ", cnt
print "wrong = ", error
print "error = ", error * 100.0 / cnt
