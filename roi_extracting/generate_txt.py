import os
import xml.etree.ElementTree as ET

from multiprocessing import cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed

# 1 class
classes = {"pos":1}

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
    
def _gen_txt(xml_name, txt_path):
    txt_name = os.path.splitext(os.path.basename(xml_name))[0] + ".txt"
    # if os.path.isfile(os.path.join(txt_path, txt_name)):
    #     return
    txt_file = open(os.path.join(txt_path, txt_name), "w")
    tree = ET.parse(xml_name)
    root = tree.getroot()
    size = root.find("size")
    w = int(size.find("width").text)
    h = int(size.find("height").text)
    
    for object_i in root.iter("object"):
        name = object_i.find("name").text
        if not name in classes:
            continue
        index = classes[name]
        bndbox = object_i.find('bndbox')
        box = (float(bndbox.find('xmin').text), 
               float(bndbox.find('xmax').text), 
               float(bndbox.find('ymin').text), 
               float(bndbox.find('ymax').text))
        box_new = ((box[0]+box[1])/2.0/w, (box[2]+box[3])/2.0/h, (box[1]-box[0])/w, (box[3]-box[2])/h)
        txt_file.write(str(index) + " " + " ".join([str(a) for a in box_new]) + "\n")
    txt_file.close()


def batch_gen_txt(xml_names, txt_path):
    for xml_name in xml_names:
        _gen_txt(xml_name, txt_path)
        
        
def gen_txt(path, dirs=("train", "test")):
    print('[info] generating txt files')
    for d in dirs:     
        txt_path = os.path.join(path, d)
    
        files = scan_files(os.path.join(path, d), postfix=".xml")
        print("# files:", len(files))

        executor = ProcessPoolExecutor(max_workers=cpu_count()//2)
        tasks = []

        batch_size = 5000
        for i in range(0, len(files), batch_size):
            batch = files[i : i+batch_size]
            tasks.append(executor.submit(batch_gen_txt, batch, txt_path))

        job_count = len(tasks)
        for future in as_completed(tasks):
            # result = future.result()  # get the returning result from calling fuction
            job_count -= 1
            print("One Job Done, Remaining Job Count: %s" % (job_count))

    
if __name__ == "__main__":
    #generate txt_list for a folder
    path = ""
    gen_txt(path)
