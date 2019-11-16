import os
from datetime import datetime
from slice import cut_cells
from rotate import do_rotate
from flip import do_flip
from generate_txt import gen_txt
from utils import generate_name_path_dict


def process(label_dict, wsi_dict, path_out, size):
    path_train = os.path.join(path_out, 'train')
    
    t1 = datetime.now()
    # cut from kfb/tif to 608 sized jpgs/labels
    cut_cells(label_dict, wsi_dict, path_train, size)

    t2 = datetime.now()
    print('[info] time cost for cell cutting:', str(t2 - t1))

    # do augmentation: rotate
    do_rotate(path_train)

    t3 = datetime.now()
    print('[info] time cost for image rotating:', str(t3 - t2))

    # do augmentation: flip
    # do_flip(path_train)

    t4 = datetime.now()
    print('[info] time cost for image flipping:', str(t4 - t3))

    # generate txt files
    gen_txt(path_out)

    t5 = datetime.now()
    print('[info] time cost for text file generating:', str(t5 - t4))
    print('[info] total time cost:', str(t5 - t1))


if __name__ == "__main__":
    label_files_path = ["../data/labels/"]
    wsi_files_path = ["../data/pos_0/", "../data/pos_1", "../data/pos_2", "../data/pos_3", "../data/pos_4", "../data/pos_5", "../data/pos_6", "../data/pos_7", "../data/pos_8", "../data/pos_9"]

    label_dict = generate_name_path_dict(label_files_path, ['.json'])
    wsi_dict = generate_name_path_dict(wsi_files_path, ['.kfb'])
    print('found {} label files and {} wsi files'.format(len(label_dict), len(wsi_dict)))

    path_out = "../data/postrain"

    process(label_dict, wsi_dict, path_out, size=608)
