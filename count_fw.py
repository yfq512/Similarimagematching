#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 13 15:30:28 2021
记录fw有效数据个数

@author: kpinfo
"""
import os
import cv2    

def auto_load_fwnpy():
    os.system('find /cmdata/files/fw/2020/ -type f > list_fw2020.txt')
    cnt = 0
    cnt1 = 1
    for n in open('list_fw2020.txt'):
        if cnt%10000 == 0:
            with open('count_fw.log','a') as f:
                f.write(str(cnt1)+','+str(cnt)+'\n')
                f.close()
        cnt = cnt + 1
        img_path = n[:-1]
        try:
            img = cv2.imread(img_path)
            img.shape
            cnt1 = cnt1 + 1
        except:
            pass

if __name__ == "__main__":
    auto_load_fwnpy()
    