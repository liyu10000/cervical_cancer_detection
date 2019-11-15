import os
import cv2
import json
import numpy as np
import kfbReader as kr


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


def get_cells(wsi, label, path):
	""" read all positive cells and save into image files
	:param wsi: kfb file name
	:param label: label file name
	:param path: image save path
	"""
	with open(label, 'r') as f:
		js = json.load(f)

	basename = os.path.splitext(os.path.basename(wsi))[0]

	scale = 20
	reader = kr.reader()
	kr.reader.ReadInfo(reader, wsi, scale, True)

	for dic in js:
		# ignore rois, use position of cells directly
		if dic['class'] == 'roi':
			continue
		img_name = '{}_{}_{}_{}_{}.jpg'.format(basename, dic['x'], dic['y'], dic['w'], dic['h'])
		img_name = os.path.join(path, img_name)
		img = reader.ReadRoi(dic['x'], dic['y'], dic['w'], dic['h'], scale)
		cv2.imwrite(img_name, img)


if __name__ == '__main__':
	sample =  "T2019_34"
	wsi =  "../data/test/" + sample + ".kfb"
	label =  "../data/test/" + sample + ".json"
	path = "../data/test/cells"
	os.makedirs(path, exist_ok=True)
	get_cells(wsi, label, path)
