#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan  7 11:22:36 2021
初始化加载本地图像为本地npy数据
分析图像根据图像三通道平均像素，白板相似度，01分布均匀程度生成路径dstpath，将[imghsah,imgpath]添加到
dstpath下的data_***_copy.npy文件中，完成更新后cp data_***_copy.npy data_***.npy，
使用时直接加载data_***.npy
@author: kpinfo
"""

import numpy as np
import cv2
import os
import fcntl

def get_pixel_name(pixel): # 输入为单通道像素均值，int类型
    names = ['0-20','15-35','30-50','45-65','60-80','75-95','90-110','105-125',
             '120-140','135-155','150-170','165-185','180-200','195-215','210-230','225-255']
    names_median = np.array([10,25,40,55,70,85,100,115,130,145,160,175,190,205,220,245])
    temp_list = np.ones(16)*pixel
    diff_abs_list = abs(names_median-temp_list)
    index_min = np.where(diff_abs_list==min(diff_abs_list))[0][0] # 如果存在多个索引，会取到第一个
    return names[index_min]

def fun_Hash(gray): # 输入为单通道图像
    # 感知哈希算法
    # 缩放32*32
    gray = cv2.resize(gray, (32, 32))   # , interpolation=cv2.INTER_CUBIC

    # 转换为灰度图
    # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 将灰度图转为浮点型，再进行dct变换
    dct = cv2.dct(np.float32(gray))
    # opencv实现的掩码操作
    dct_roi = dct[0:8, 0:8]

    hash_ = []
    avreage = np.mean(dct_roi)
    for i in range(dct_roi.shape[0]):
        for j in range(dct_roi.shape[1]):
            if dct_roi[i, j] > avreage:
                hash_.append(1)
            else:
                hash_.append(0)
    # 输出为hash列表
    return hash_

def fun_Hash2(gray): # 输入为单通道图像
    # 均值冒泡
    # 缩放32*32
    gray = cv2.resize(gray, (8, 8))   # , interpolation=cv2.INTER_CUBIC
    hash_ = []
    avreage = np.mean(gray)
    for i in range(gray.shape[0]):
        for j in range(gray.shape[1]):
            if gray[i, j] > avreage:
                hash_.append(1)
            else:
                hash_.append(0)
    # 输出为hash列表
    return hash_

def get_similar_name(hash_sum): # 输入为图像指纹list.sum,或者冒泡指纹sum
    names = ['0-6','4-10','8-14','12-18','16-22','20-26','24-30','28-34','32-38','36-42',
             '40-46','44-50','48-54','52-58','56-64']
    names_median = np.array([3,7,11,15,19,23,27,31,35,39,43,47,51,55,60])
    temp_list = np.ones(15)*hash_sum
    diff_abs_list = abs(names_median-temp_list)
    index_min = np.where(diff_abs_list==min(diff_abs_list))[0][0] # 如果存在多个索引，会取到第一个
    return names[index_min]

def get_img_name(img, dstpath): # 单筒单灰度图像，路径规则为:dstpath/B*/G*/R*/Similar*/mean*/data_B*_G*_R*_Similar*_mean*_copy.npy
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_b, img_g, img_r = img[:,:,0], img[:,:,1], img[:,:,2]
    name_b = get_pixel_name(int(img_b.mean()))
    name_b = 'B-'+name_b
    name_g = get_pixel_name(int(img_g.mean()))
    name_g = 'G-'+name_g
    name_r = get_pixel_name(int(img_r.mean()))
    name_r = 'R-'+name_r
    
    hash1 = fun_Hash(gray)
    hash2 = fun_Hash2(gray)
    name_similar = get_similar_name(sum(hash1))
    name_similar = 'Similar-'+name_similar
    name_mean = get_similar_name(sum(hash2))
    name_mean = 'Mean-'+name_mean
    out_path = os.path.join(dstpath, name_b, name_g, name_r, name_similar, name_mean)
    return out_path

if __name__ == "__main__":
    root = 'imgs_es'
    dstroot = './data_npy'
    npy_work_name = 'data.npy'
    npy_copy_name = 'data_copy.npy'
    imglist = os.listdir(root)
    cnt = 0
    for n in imglist:
        cnt = cnt + 1
        imgpath = os.path.join(root, n)
        img = cv2.imread(imgpath)
        try:
            img.shape
        except:
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hash_str = fun_Hash(gray)
        out_path = get_img_name(img, dstroot)
        if not os.path.exists(out_path):
            os.makedirs(out_path)
        data_npy_path = os.path.join(out_path, npy_copy_name)
        if not os.path.exists(data_npy_path): # 若不存在则新建
            data = {'imghash':[hash_str],'imgpath':[n]}
            np.save(data_npy_path, data)
        else:
            f1 = open(data_npy_path)
            fcntl.flock(f1,fcntl.LOCK_EX) # 获取锁
            data = np.load(data_npy_path, allow_pickle=True).item()
            imghash_list = data.get('imghash')
            imgpath_list = data.get('imgpath')
            imghash_list.append(hash_str)
            imgpath_list.append(n)
            np.save(data_npy_path, data)
            fcntl.flock(f1,fcntl.LOCK_UN) # 解除锁
        print(cnt, out_path)