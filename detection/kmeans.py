import os
import pickle
import numpy as np
from sklearn.cluster import KMeans, MiniBatchKMeans

from multiprocessing import cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed



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

def collect_sizes(txt_fname, size):
    sizes = []
    with open(txt_fname, 'r') as f:
        for line in f.readlines():
            tokens = line.strip().split()
            sizes.append([int(float(tokens[3])*size), int(float(tokens[4])*size)])
    return sizes

def batch_collect_sizes(txt_fnames, size):
    sizes = []
    for txt_fname in txt_fnames:
        sizes += collect_sizes(txt_fname, size)
    return sizes

def worker_single(data_path, size=608):
    txt_fnames = scan_files(data_path, postfix=".txt")
    sizes = []
    for i,txt_fname in enumerate(txt_fnames):
        if i % 10000 == 0:
            print(i)
        sizes += collect_sizes(txt_fname, size)
    return sizes

def get_file(data_path):
    if os.path.isdir(data_path):
        files = scan_files(data_path, postfix=".txt")
    else:
        files = []
        with open(data_path, 'r') as f:
            for line in f.readlines():
                files.append(os.path.splitext(line.strip())[0] + ".txt")
    return files

def worker_multip(data_path, size=608):
    files = get_file(data_path)
    print("# files:", len(files))

    executor = ProcessPoolExecutor(max_workers=8)
    tasks = []

    batch_size = 10000
    for i in range(0, len(files), batch_size):
        batch = files[i : i+batch_size]
        tasks.append(executor.submit(batch_collect_sizes, batch, size))
    
    sizes = []
    job_count = len(tasks)
    for future in as_completed(tasks):
        result = future.result()  # get the returning result from calling fuction
        sizes += result
        job_count -= 1
        print("One Job Done, Remaining Job Count: %s, Files collected: %d" % (job_count, len(sizes)))
        
    return sizes


def kmeans_cluster(features, K, batch_size):
    X = np.asarray(features)
    estimator = MiniBatchKMeans(n_clusters=K, random_state=1, batch_size=batch_size, compute_labels=True)
    estimator.fit(X)
    return estimator.cluster_centers_


if __name__ == '__main__':
    data_path = "../data/postrain/train.txt"
    sizes = worker_multip(data_path)
    print("# files", len(sizes))

    # save file
    pkl_file = "../data/postrain/sizes.pkl"
    with open(, 'wb') as f:
        pickle.dump(sizes, f)

    # kmeans
    cluster_centers_ = kmeans_cluster(sizes, K=15, batch_size=128)
    centers = []
    for center in cluster_centers_:
        print(center)
        centers.append(center)
    
    # sort and print centers
    tosort = {int(center[0]*center[1]):center for center in centers}
    hassorted = sorted(tosort.items())
    print(",  ".join(["{},{}".format(int(value[1][0]),int(value[1][1])) for value in hassorted]))
