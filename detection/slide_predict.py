import os
import cv2
import time
import random
import numpy as np
import json
import darknet as dn

from multiprocessing import cpu_count
from multiprocessing import Process, Queue
from multiprocessing import Pool, Manager

from concurrent.futures import ProcessPoolExecutor, as_completed

import kfbReader as kr
from gen_xml import Xml


# 选中一个大图，运行切图程序，
# （1）得到切图的坐标。（2）根据坐标去切图 （3）对切出的每一个图检测 （4）保存检测到的细胞，并收集所有结果。（5）保存大图结果。


cfg = "cfg/yolov3-spp.cfg".encode("utf-8")
weights = "cfg/yolov3-spp_170000.weights".encode("utf-8")
data = "cfg/tianchi_tct.data".encode("utf-8")

def scan_files(directory, prefix=None, postfix=None):
    files_list = []
    for root, sub_dirs, files in os.walk(directory):
        for special_file in files:
            if postfix:
                if special_file.endswith(postfix):
                    files_list.append(os.path.join(root, special_file))
            elif prefix:
                if special_file.startswith(prefix):
                    files_list.append(os.path.join(root, special_file))
            else:
                files_list.append(os.path.join(root, special_file))
    return files_list


def array_to_image(arr):
    # need to return old values to avoid python freeing memory
    arr = arr.transpose(2,0,1)
    c, h, w = arr.shape[0:3]
    arr = np.ascontiguousarray(arr.flat, dtype=np.float32) / 255.0
    data = arr.ctypes.data_as(dn.POINTER(dn.c_float))
    im = dn.IMAGE(w,h,c,data)
    return im, arr

def detect3(net, meta, image, thresh=.5, hier_thresh=.5, nms=.45):
    if isinstance(image, bytes):  
        # image is a filename 
        # i.e. image = b'/darknet/data/dog.jpg'
        im = load_image(image, 0, 0)
    else:  
        # image is an nparray
        # i.e. image = cv2.imread('/darknet/data/dog.jpg')
        im, image = array_to_image(image)
        dn.rgbgr_image(im)
    num = dn.c_int(0)
    pnum = dn.pointer(num)
    dn.predict_image(net, im)
    dets = dn.get_network_boxes(net, im.w, im.h, thresh, 
                             hier_thresh, None, 0, pnum)
    num = pnum[0]
    if nms: dn.do_nms_obj(dets, num, meta.classes, nms)

    res = []
    for j in range(num):
        a = dets[j].prob[0:meta.classes]
        if any(a):
            ai = np.array(a).nonzero()[0]
            for i in ai:
                b = dets[j].bbox
                res.append((meta.names[i], dets[j].prob[i], 
                           (b.x, b.y, b.w, b.h)))

    res = sorted(res, key=lambda x: -x[1])
    if isinstance(image, bytes): free_image(im)
    dn.free_detections(dets, num)
    return res
    
    
def get_coord(q_coord, w, h):
    
    x = [i for i in range(int(w/5), w-int(w/6), 600)]
    y = [j for j in range(int(h/5), h-int(h/6), 600)]
    coord = [(m,n) for m in x for n in y]
    for item in coord:
        q_coord.put(item)
    for i in range(16):
        q_coord.put((None, None))
    
def get_img_608(q_img, q_coord, f):
    scale = 20
    reader = kr.reader()
    kr.reader.ReadInfo(reader, f, scale, True)
    
    size = 608
    while True:
        (x, y) = q_coord.get()
        if x == None:
            break
        cell = reader.ReadRoi(x, y, size, size, scale)
        q_img.put((cell, x, y))
    for i in range(4):
        q_img.put((None, None, None))
        
def predict_608(q_res, q_img, i):
    dn.set_gpu(i)
    net = dn.load_net(cfg, weights,0)
    meta = dn.load_meta(data)
    while True:
        (cell, x, y) = q_img.get()
        if x == None:
            break
        det = detect3(net, meta, cell)
        if len(det) == 0:
            continue
        for d in det:
            p = d[1]
            x_ = d[2][0]+x-304
            y_ = d[2][1]+y-304
            w  = d[2][2]
            h  = d[2][3]
            if w*h<500:
                continue
            
            # q_res.put({"x":x_, "y":y_, "w":w, "h":h, "p":p})
            
            # save image.
            l = int(d[2][0]-w/2 + 0.5)
            r = int(l + w + 0.5)
            hi = int(d[2][1]-h/2 + 0.5)
            lo = int(hi + h+0.5)
            tmp = cell[l:r,hi:lo,:]
            var = np.var(tmp)

            if var < 1250:
                continue
            
            q_res.put({"x":x_, "y":y_, "w":w, "h":h, "p":p})
            
            # cv2.imwrite("./result/pos/"+str(w)+"_"+str(h)+".bmp", cell[l:r,hi:lo,:])

            
            
    for i in range(1):
        q_res.put(None)
        
def get_result(q_res,f):
    base = os.path.basename(f).split(".")[0]
    save_path = "./result/tianchi2/"+base+".json"
    res = []
    while True:
        r = q_res.get()
        if r == None:
            break
        res.append(r)
    
    with open(save_path, "w") as f:
        json.dump(res, f)
    

def start_processes(all_processes):
    for ps in all_processes:
        for p in ps:
            p.start()
def join_processes(all_processes):
    for ps in all_processes:
        for p in ps:
            p.join()
            
            
def predict_slide(f):
    # q_coord = Queue(maxsize=4096)
    # q_img   = Queue(maxsize=4096)
    # q_res   = Queue(maxsize=4096)
    
    q_coord = Manager().Queue(4096)
    q_img   = Manager().Queue(4096)
    q_res   = Manager().Queue(4096)
    
    
    scale = 20
    reader = kr.reader()
    kr.reader.ReadInfo(reader, f, scale, True)
    height = reader.getHeight()
    width = reader.getWidth()
    #print(height, width)
    
    # p_coord = []
    # p_img = []
    # p_res = []
    # p_save = []

    # p_coord.append(Process(target=get_coord, args=(q_coord,height, width,)))
    # for i in range(16):
        # p_img.append(Process(target=get_img_608, args=(q_img,q_coord,f, )))
    # for i in range(4):
        # p_res.append(Process(target=predict_608, args=(q_res, q_img, i, )))    
    # p_save.append(Process(target=get_result, args=(q_res,f, )))
    # # start processes    
    # start_processes([p_coord, p_img, p_res, p_save])
    # # join processes
    # join_processes([p_coord, p_img, p_res, p_save])
    
    p = Pool(22)
    p.apply_async(func=get_coord, args=(q_coord,height, width,))
    for i in range(16):
        p.apply_async(func=get_img_608, args=(q_img,q_coord,f, ))
    for i in range(4):
        p.apply_async(func=predict_608, args=(q_res, q_img, i, ))
    p.apply_async(func=get_result, args=(q_res,f, ))
    p.close()
    p.join()    


def run(path):
    files = scan_files(path, postfix = "kfb")
    random.shuffle(files)
    for f in files:
        base = os.path.basename(f).split(".")[0]
        save_path = "./result/tianchi2/"+base+".json"
        if os.path.exists(save_path):
            continue
        predict_slide(f)


if __name__ == "__main__":
    
    path = "/home/nvme2T/mpc/project/TCT/data/test/"
    run(path)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
