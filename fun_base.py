import cv2
import numpy as np

def fun_Hash(img): # 输入为RGB三通道图像
    # 感知哈希算法
    # 缩放32*32
    img = cv2.resize(img, (32, 32))   # , interpolation=cv2.INTER_CUBIC

    # 转换为灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
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

def com2hashstr(hash1, hash2): # 计算两个哈希值的相似度
    if len(hash1) != len(hash2):
        return -1
    n = 0
    for i in range(len(hash1)):
        if hash1[i] != hash2[i]:
            n = n + 1
    n = sorce_remap(n, 0, 64, -1)
    return n

def sorce_remap(value, limit1, limit2, sign): # 将相似度映射到0，1之间
    N_long = 100/(limit2 - limit1)
    if sign == 1:
        #return float(value*N_long/100)
        return value*N_long
    elif sign == -1:
        #return float((100 - value*N_long)/100)
        return 100 - value*N_long
