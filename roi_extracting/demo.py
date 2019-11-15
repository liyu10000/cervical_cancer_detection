import kfbReader as kr
import os
import cv2
import numpy as np
import json

scale =  20
sample =  "T2019_34"

file1 =  "./"+sample+".kfb"
label1 =  "./"+sample+".json"
dir = './rois/'
os.makedirs(dir, exist_ok=True)
reader = kr.reader()
kr.reader.ReadInfo(reader,file1,scale,True)

def  get_roi(label):
	with  open(label,"r") as f:
		js = json.load(f)
	rois = []
	roi = {}
	for dic in js:
		if dic["class"] ==  "roi":
			roi = dic
			roi["poses"] = []
			rois.append(roi)
		else :
			pass
	for dic in js:
		if dic["class"] ==  "roi":
			pass
		else:
			for roi1 in rois:
				if roi1["x"] <= dic["x"] and roi1["y"] <= dic["y"] and dic["x"] + dic["w"] <= roi1["x"] + roi1["w"] and dic["y"] + dic["h"] <= roi1["y"] + roi1["h"]:
					roi1["poses"].append(dic)
	return rois
	
rois = get_roi(label1)
print(len(rois))

for i,roi1 in  enumerate(rois):
	roi = reader.ReadRoi(roi1["x"],roi1["y"],roi1["w"],roi1["h"],scale)
	for pos in roi1["poses"]:
		rx = pos["x"]-roi1["x"]
		ry = pos["y"]-roi1["y"]
		cv2.rectangle(roi, (rx,ry), (rx+pos["w"],ry+pos["h"]),(0,255,0), 4)
	save_name =  dir+str(i)+".jpg"
	cv2.imwrite(save_name,roi)
	print("save roi img:"+save_name)
