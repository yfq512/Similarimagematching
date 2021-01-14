#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 13 15:30:28 2021
1. find file1 -type f > list.txt 生成所有文件列表，记录当前时间T1；
2. 遍历list.txt，取得T0，得到文件创建时间T2，若T2旧于T0，则跳过；否则导入npy；
3. 遍历结束后，3600*12s后再循环

@author: kpinfo
"""
import os
import time 
import cv2    
from init_load_img2npy import auto_updata_imgnpy as load_imgnpy
from auto_loadimgnpy import compare_time

def auto_load_fwnpy(timerecord_txt = 'time_record.txt', outfile_txt = 'list_fw2020.txt'):
    while True:
        if os.path.exists(outfile_txt): # 清除图像路径文件
            os.remove(outfile_txt)
        time_record_list = []
        for n in open(timerecord_txt): # 获取最后更新时间
            line = n[:-1]
            time_record_list.append(line)
        last_time = time_record_list[-1]
        now_time = time.strftime("%F %H:%M:%S") ##24小时格式
        with open(timerecord_txt, 'a') as f:
            f.write(now_time)
            f.write('\n')
            f.close()
        os.system('find /cmdata/files/fw/2020/ -type f > list_fw2020.txt')
        while True:
            if os.path.exists(outfile_txt):
                break
            else:
                time.sleep(1)
                continue
        cnt1 = 0
        cnt2 = 0
        for m in open(outfile_txt):
            print(cnt1, cnt2)
            cnt1 = cnt1 + 1
            line = m[:-1]
            creat_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.stat(line).st_ctime))
            if compare_time(last_time, creat_time):
                try:
                    img = cv2.imread(line)
                    img.shape
                except:
                    str1 = 'failed load npt,' + line
                    with open('fw_load_failed.log','a') as f1:
                        f1.write(str1)
                        f1.write('\n')
                        f1.close()
                # load npy
                sign = load_imgnpy(line)
                if sign == -1:
                    with open('fw_load_failed.log','a') as f1:
                        f1.write(str1)
                        f1.write('\n')
                        f1.close()
                else:
                    cnt2 = cnt2 + 1
                    with open('load_fw_record.log','a') as f2:
                        f2.write(line)
                        f2.write('\n')
                        f2.close()
            else:
                continue
        time.sleep(3600*12)

if __name__ == "__main__":
    auto_load_fwnpy()