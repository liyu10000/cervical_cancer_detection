import os
import shutil
import random
from PIL import Image


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


def cut_cells(txt_name, size, save_path):
    img_name = os.path.splitext(txt_name)[0] + ".bmp"
    
    boxes = []
    with open(txt_name, 'r') as f:
        for line in f.readlines():
            tokens = line.strip().split()
            cx, cy = float(tokens[1])*size, float(tokens[2])*size
            w, h = int(float(tokens[3])*size), int(float(tokens[4])*size)
            x, y = int(cx - w/2), int(cy - h/2)
            boxes.append([x, y, w, h])
    
#     if len(boxes) == 1:
#         return

    basename = os.path.splitext(os.path.basename(txt_name))[0]
    with Image.open(img_name) as img:
        for box in boxes:
            x, y, w, h = box
            jpg_name = os.path.join(save_path, "{}_{}_{}_{}_{}.jpg".format(basename, x, y, w, h))
            print(len(boxes), jpg_name)
            img.crop((box[0], box[1], box[0]+box[2], box[1]+box[3])).save(jpg_name)


if __name__ == '__main__':
    data_path = "../data/postrain"
    save_path = "../data/poscells"
    os.makedirs(save_path, exist_ok=True)
    all_txt_names = scan_files(data_path, postfix=".txt")

    txt_names = random.sample(all_txt_names, 100)
    # txt_names = all_txt_names

    for txt_name in txt_names:
        cut_cells(txt_name, 608, save_path)
