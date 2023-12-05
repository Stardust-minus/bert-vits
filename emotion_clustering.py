from sklearn.cluster import *
from sklearn import metrics
from sklearn.mixture import GaussianMixture  # 高斯混合模型
import os
import numpy as np
from config import config
import yaml
import argparse
from multiprocessing import Pool
from tqdm import tqdm

def process_speaker(speaker):
    embs = []
    wavnames = []
    print("\nspeaker: "+speaker)
    for file in filelist_dict[speaker]:
        try:                   
            embs.append(np.expand_dims(np.load(f"{os.path.splitext(file)[0]}.emo.npy"), axis=0))
            wavnames.append(os.path.basename(file))
        except Exception as e:
            print(e)
    x = np.concatenate(embs,axis=0)
    x = np.squeeze(x)
    # 聚类算法类的数量
    n_clusters = args.num_clusters
    if args.algorithm=="b":
        model = Birch(n_clusters= n_clusters, threshold= 0.2)
    elif args.algorithm=="s":
        model = SpectralClustering(n_clusters=n_clusters)
    elif  args.algorithm=="a":
        model = AgglomerativeClustering(n_clusters= n_clusters)
    else: 
        model = KMeans(n_clusters=n_clusters, random_state=10)
    # 可以自行尝试各种不同的聚类算法
    y_predict = model.fit_predict(x)
    classes=[[] for i in range(y_predict.max()+1)]

    for idx, wavname in enumerate(wavnames):
        classes[y_predict[idx]].append(wavname)

    yml_result = {}
    yml_result[speaker]={}
    for i in range(y_predict.max()+1):
        class_length=len(classes[i])
        print("类别:", i, "本类中样本数量:", class_length)
        yml_result[speaker][f"class{i}"]=[]
        for j in range(args.range):
            if j >=class_length:
                break
            print(classes[i][j])  
            yml_result[speaker][f"class{i}"].append(classes[i][j])
    if hasattr(model, 'cluster_centers_') and config.emo_cluster_config.save_center:
        centers = model.cluster_centers_
        os.makedirs(os.path.join(config.dataset_path, f'emo_clustering/{speaker}'), exist_ok=True)
        for i in range(centers.shape[0]):
            # 为每个中心创建一个文件名
            filename = os.path.join(config.dataset_path, f'emo_clustering/{speaker}/cluster_center_{i}.npy')
        # 保存中心
        np.save(filename, centers[i])
    return yml_result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-a","--algorithm", default="k",help="choose algorithm",type=str)
    parser.add_argument("-n","--num_clusters", default=3,help="number of clusters",type=int)
    parser.add_argument("-r","--range", default=4,help="number of files in a class",type=int)
    args = parser.parse_args()
    filelist_dict={}
    with open(config.preprocess_text_config.train_path, mode="r", encoding="utf-8") as f:
        for line in f:
            speaker=line.split("|")[1]
            if speaker not in filelist_dict:
                filelist_dict[speaker]=[]
            filelist_dict[speaker].append(line.split("|")[0]) 

    with Pool() as p:
        results = list(tqdm(p.imap(process_speaker, list(filelist_dict.keys())), total=len(filelist_dict)))

    yml_result = {}
    for result in results:
        yml_result.update(result)

    with open(os.path.join(config.dataset_path,'emo_clustering.yml'), 'w', encoding='utf-8') as f:
        yaml.dump(yml_result, f)
