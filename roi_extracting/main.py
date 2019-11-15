import os
from slice import cut_cells
from rotate import do_rotate
from flip import do_flip
from generate_txt import gen_txt
from utils import generate_name_path_dict


def process(label_dict, wsi_dict, path_out, size):
    path_train = os.path.join(path_out, 'train')
      
    # cut from kfb/tif to 608 sized jpgs/labels
    cut_cells(label_dict, wsi_dict, path_train, size)

    # do augmentation: rotate
    do_rotate(path_train)

    # do augmentation: flip
    # do_flip(path_train)

    # generate txt files
    gen_txt(path_out)


if __name__ == "__main__":
    label_files_path = ["../data/test/"]
    wsi_files_path = ["../data/test/"]

    label_dict = generate_name_path_dict(label_files_path, ['.json'])
    wsi_dict = generate_name_path_dict(wsi_files_path, ['.kfb'])
    print('found {} label files and {} wsi files'.format(len(label_dict), len(wsi_dict)))

    path_out = "../data/test/sampledata"

    process(label_dict, wsi_dict, path_out, size=608)
