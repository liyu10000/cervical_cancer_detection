# test
./darknet detector test cfg/pos.data cfg/pos.cfg yolov3.weights data/dog.jpg
# train
./darknet detector train cfg/pos.data cfg/pos.cfg yolov3.weights -gpus 0,1
