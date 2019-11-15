# coding=utf-8
import os
import cv2
import numpy as np
import json

from multiprocessing import cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed

import kfbReader as kr
from gen_xml import Xml


def get_labels(label_file):
    with open(label_file, 'r') as f:
        js = json.load(f)

    labels = {}
    i = 0
    for dic in js:
        if dic['class'] == 'roi':
            continue
        x, y, w, h = dic['x'], dic['y'], dic['w'], dic['h']
        x_min, x_max, y_min, y_max = x, x+w, y, y+h
        labels[i] = (x_min, x_max, y_min, y_max, 'pos')  # only one class pos here
        i += 1
    return labels


# get windows in wsi that contain labels
def get_windows_new(labels, size):
    """
        labels: {i:(x_min, x_max, y_min, y_max, class)}
        size: image size to crop
        return: {(x, y):[i,]}
    """
    graphs_xy = []

#       p0   p1   p2        # graph0_pointxy = p0.x         , p0.y
#       -------------       # graph1_pointxy = p1.x - 303   , p1.y
#       |           |       # graph2_pointxy = p2.x - 607   , p2.y
#       |           |       # graph3_pointxy = p3.x         , p3.y - 303
#    p3 |    p4   p5|       # graph4_pointxy = p4.x - 303   , p4.y - 303
#       |           |       # graph5_pointxy = p5.x - 607   , p5.y - 303
#       |           |       # graph6_pointxy = p6.x         , p6.y - 607
#       -------------       # graph7_pointxy = p7.x - 303   , p7.y - 607
#       p6   p7   p8        # graph8_pointxy = p8.x - 607   , p8.y - 607

# P0 = x_min, y_min
# p1 = (x_max - x_min)/2, ymin
# p2 = x_max, y_min
# p3 = x_min, (y_max - y_min)/2
# p4 = (x_max - x_min)/2, (y_max - y_min)/2
# p5 = x_max, (y_max - y_min)/2
# p6 = x_min, y_max
# p7 = (x_max - x_min)/2, y_max
# p8 = x_max, y_max

    big_count = 0
    small_count = 0

# 1 / 3 size of the small pic
    size_3 = int(size / 3) 
    size_2 = int(size / 2)
    size_1 = size

    for i, label in labels.items():

        x_min = label[0]
        x_max = label[1]
        y_min = label[2]
        y_max = label[3]

        label_max_size = max(x_max - x_min, y_max - y_min)
        label_size_x = x_max - x_min
        label_size_y = y_max - y_min


        p0 = (x_min,                            y_min)
        p1 = (int((x_max + x_min)/2),           y_min)
        p2 = (x_max,                            y_min)
        p3 = (x_min,                            int((y_max + y_min)/2))
        p4 = (int((x_max + x_min)/2),           int((y_max + y_min)/2))
        p5 = (x_max,                            int((y_max + y_min)/2))
        p6 = (x_min,                            y_max)
        p7 = (int((x_max + x_min)/2),           y_max)
        p8 = (x_max,                            y_max)

        # graph0 ~ 9

        # ok
        if ((label_size_x > size_3) and (label_size_y > size_3)):
            
            graphs_xy.append([x_min,                y_min])
            graphs_xy.append([p4[0] - size_2 + 1,   y_min])
            graphs_xy.append([x_max - size_1,       y_min])
            
            graphs_xy.append([x_min,                p4[1] - size_2])
            graphs_xy.append([p4[0] - size_2 + 1,   p4[1] - size_2])
            graphs_xy.append([x_max - size_1,       p4[1] - size_2])
            
            graphs_xy.append([x_min,                y_max - size_1])
            graphs_xy.append([p4[0] - size_2 + 1,   y_max - size_1])
            graphs_xy.append([x_max - size_1,       y_max - size_1])

        if ((label_size_x > size_3) and (label_size_y <= size_3)):
            graphs_xy.append([x_min,                p4[1] - int(size / 6)])
            graphs_xy.append([p4[0] - size_2 + 1,   p4[1] - int(size / 6)])
            graphs_xy.append([x_max - size_1,       p4[1] - int(size / 6)])

            graphs_xy.append([x_min,                p4[1] - int(size / 2)])
            graphs_xy.append([p4[0] - size_2 + 1,   p4[1] - int(size / 2)])
            graphs_xy.append([x_max - size_1,       p4[1] - int(size / 2)])
            
            graphs_xy.append([x_min,                p4[1] - int((size / 6) * 5)])
            graphs_xy.append([p4[0] - size_2 + 1,   p4[1] - int((size / 6) * 5)])
            graphs_xy.append([x_max - size_1,       p4[1] - int((size / 6) * 5)])
            
            big_count = big_count + 1

        if ((label_size_x <= size_3) and (label_size_y > size_3)):
            graphs_xy.append([p4[0] - int(size / 6),        y_min])
            graphs_xy.append([p4[0] - int(size / 2),        y_min])
            graphs_xy.append([p4[0] - int((size / 6) * 5),  y_min])

            
            graphs_xy.append([p4[0] - int(size / 6),        p4[1] - size_2])
            graphs_xy.append([p4[0] - int(size / 2),        p4[1] - size_2])
            graphs_xy.append([p4[0] - int((size / 6) * 5),  p4[1] - size_2])
            
            graphs_xy.append([p4[0] - int(size / 6),        y_max - size_1])
            graphs_xy.append([p4[0] - int(size / 2),        y_max - size_1])
            graphs_xy.append([p4[0] - int((size / 6) * 5),  y_max - size_1])
            
            big_count = big_count + 1

        if ((label_size_x <= size_3) and (label_size_y <= size_3)):
            graphs_xy.append([p4[0] - int(size / 6),        p4[1] - int(size / 6)])
            graphs_xy.append([p4[0] - int(size / 2),        p4[1] - int(size / 6)])
            graphs_xy.append([p4[0] - int((size / 6) * 5),  p4[1] - int(size / 6)])
            graphs_xy.append([p4[0] - int(size / 6),        p4[1] - int(size / 2)])
            graphs_xy.append([p4[0] - int(size / 2),        p4[1] - int(size / 2)])
            graphs_xy.append([p4[0] - int((size / 6) * 5),  p4[1] - int(size / 2)])
            graphs_xy.append([p4[0] - int(size / 6),        p4[1] - int((size / 6) * 5)])
            graphs_xy.append([p4[0] - int(size / 2),        p4[1] - int((size / 6) * 5)])
            graphs_xy.append([p4[0] - int((size / 6) * 5),  p4[1] - int((size / 6) * 5)])

            small_count = small_count + 1


    points_xy = {}
    x, y = 0, 0
    for xy in graphs_xy:
        x = xy[0]
        y = xy[1]

        for i, label in labels.items():
            if (x <= label[0] and label[1] <= x+size and y <= label[2] and label[3] <= y+size) or \
                ((label[0] <= x and x+size <= label[1]) and (label[2] <= y and y+size <= label[3])) or \
                ((label[0] <= x and x+size <= label[1]) and (y <= label[2] and label[3] <= y+size)) or \
                ((x <= label[0] and label[1] <= x+size) and (label[2] <= y and y+size <= label[3])):
                if (x, y) in points_xy:
                    points_xy[(x, y)].append(i)
                else:
                    points_xy[(x, y)] = [i,]


    print("################### big_cells count is ", big_count)
    print("################### small_cells count is ", small_count)

    print("################### graph num is ", len(graphs_xy))
    print("################### point num is ", len(points_xy))

    return points_xy



def hls_trans_smart(image, HLS_L=[0.9], HLS_S=[0.4, 0.5]):
    # image = cv2.imread(image_name)
    # image = np.asarray(image)

    # 图像归一化，且转换为浮点型
    hlsImg = image.astype(np.float32)
    hlsImg = hlsImg / 255.0
    # 颜色空间转换 BGR转为HLS
    hlsImg = cv2.cvtColor(hlsImg, cv2.COLOR_BGR2HLS)
    
    # 1.调整亮度
    l = np.average(hlsImg[:,:,1])
    i = len(HLS_L) - 1
    while i != -1 and HLS_L[i] > l:
        i -= 1
    if i != len(HLS_L)-1:
        hls_l = HLS_L[i+1]
        hlsImg[:, :, 1] = hls_l / l * hlsImg[:, :, 1]
        hlsImg[:, :, 1][hlsImg[:, :, 1] > 1] = 1
        # print(image_name, "changing l", l, "to", hls_l)
        
    # 2.调整饱和度
    s = np.average(hlsImg[:,:,2])
    i = len(HLS_S) - 1
    while i != -1 and HLS_S[i] > s:
        i -= 1
    if i != len(HLS_S)-1:
        hls_s = HLS_S[i+1]
        hlsImg[:, :, 2] = hls_s / s * hlsImg[:, :, 2]
        hlsImg[:, :, 2][hlsImg[:, :, 2] > 1] = 1
        # print(image_name, "changing s", s, "to", hls_s)
        
    # HLS2BGR
    hlsImg = cv2.cvtColor(hlsImg, cv2.COLOR_HLS2BGR)
    # 转换为8位unsigned char
    hlsImg = hlsImg * 255
    image = hlsImg.astype(np.uint8)
    
    return image



def cell_sampling(label_file, wsi_path, save_path, size):

    labels = get_labels(label_file)
    if len(labels) == 0:
        return

    print("PROCESSING %s ..." % wsi_path)

    scale = 20
    reader = kr.reader()
    kr.reader.ReadInfo(reader, wsi_path, scale, True)

    points_xy = get_windows_new(labels, size)
    filename, _ = os.path.splitext(os.path.basename(wsi_path))

    # generate img files
    points_num = len(points_xy)
    for i, (x, y) in enumerate(points_xy):
        if ((i % 100) == 0):
            print(filename, "processed #", i)
        cell = reader.ReadRoi(x, y, size, size, scale)
        
        image_file_name = save_path + "/" + filename + "_" + str(x) + "_" + str(y) + ".bmp"
        
        # change l and s of image
        # cell = hls_trans_smart(cell)
        
        cv2.imwrite(image_file_name, cell)

    # generate xml files
    print(filename, "generating xml")
    new_xmls = Xml(filename, save_path, points_xy, labels, size)
    new_xmls.gen_xml()

    print("[INFO]", "processed ", xml_file)

    
def cut_cells(label_dict, wsi_dict, path_out, size):
    os.makedirs(path_out, exist_ok=True)

    executor = ProcessPoolExecutor(max_workers=cpu_count()//2)
    tasks = []

    for key, label_path in label_dict.items():
        if key in wsi_dict:
            wsi_path = wsi_dict[key]
            # cell_sampling(label_path, wsi_path, path_out, size)
            tasks.append(executor.submit(cell_sampling, label_path, wsi_path, path_out, size))
        else:
            print("### ERROR ### %s IS NOT FOUND IN wsi_DICT" % key)

    job_count = len(tasks)
    for future in as_completed(tasks):
        # result = future.result()  # get the returning result from calling fuction
        job_count -= 1
        print("One Job Done, Last Job Count: %s" % (job_count))            



if __name__ == "__main__":
    label_file = "../data/labels/T2019_34.json"
    
    labels = get_labels(label_file)
    print(labels)
    
    pass

