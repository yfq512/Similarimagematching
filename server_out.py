# coding=utf-8
import cv2, os, time, random, base64, shutil, fcntl, re, json
from fun_base import com2hashstr
from flask import Flask,render_template,request
from elasticsearch import Elasticsearch
from init_load_img2npy import get_img_name
from init_load_img2npy import fun_Hash
import numpy as np
from init_load_img2npy import auto_updata_imgnpy as load_imgnpy

def getRandomSet(bits):
    num_set = [chr(i) for i in range(48,58)]
    char_set = [chr(i) for i in range(97,123)]
    total_set = num_set + char_set
    value_set = "".join(random.sample(total_set, bits))
    return value_set
def get_limit_imgpath(dstimgpath, limit):
    limit = int(limit)
    dstimg = cv2.imread(dstimgpath)
    try:
        dstimg.shape
    except:
        print('img read error')
        return -1, [],[]
    dstimg_gray = cv2.cvtColor(dstimg, cv2.COLOR_BGR2GRAY)
    dstimg_2 = cv2.flip(dstimg, 1) # check overturn image on the same time
    dstimg_gray2 = cv2.cvtColor(dstimg_2, cv2.COLOR_BGR2GRAY)

    # 获取目标图像所在特征组路径
    out_path = get_img_name(dstimg, './data_npy')
    data_npy_path = os.path.join(out_path, 'data_copy.npy')
    # 获取特征列表和图像名列表
    if os.path.exists(data_npy_path):
        while True:
            try:
                data_npy = np.load(data_npy_path, allow_pickle=True).item()
                _hash_strs = data_npy.get('imghash')
                _imgpaths = data_npy.get('imgpath')
                break
            except:
                print('>>> read error, time sleep 1s and read data again!')
                time.sleep(1)
    else:
        _hash_strs = []
        _imgpaths = []

    dst_hash_str = fun_Hash(dstimg_gray)
    dst_hash_str_2 = fun_Hash(dstimg_gray2)
    out_imgpaths = []
    similar_scores = []
    for n in range(len(_hash_strs)):
        temp_value = com2hashstr(dst_hash_str, _hash_strs[n])
        temp_value_2 = com2hashstr(dst_hash_str_2, _hash_strs[n])
        temp_value = max(temp_value, temp_value_2) # use max score
        if temp_value > limit:
            out_imgpaths.append(_imgpaths[n])
            similar_scores.append(temp_value)
    #if add online img
    _cnt1 = 0
    for xxx in out_imgpaths:
        _split = xxx.split('@#$!!')
        if len(_split) > 1:
            continue
        else:
            _cnt1 = _cnt1 + 1
    if _cnt1 == len(out_imgpaths):
        load_imgnpy(dstimgpath)
        cv2.imwrite(os.path.join('online',dstimgpath),dstimg)

    # 查询es数据库，返回similar_infos
    similar_infos = []
    for img_name_index in range(len(out_imgpaths)):
        img_name = out_imgpaths[img_name_index]
        print('11111111111', img_name)
        img_name_split_online = img_name.split('@#$!!')
        if len(img_name_split_online) > 1:
            img_url = None
            title = out_imgpaths[img_name_index]
            title_url = None
            web_source = None
            img_similar_score = similar_scores[img_name_index]
            id_title = None
            all_imgs = None
        else:
            img_name_split = img_name.split('@#$!')
            if len(img_name_split) > 1: # fw数据，基于id查询
                _id = img_name_split[0]
                
                body = {
                    "query":{
                        "match":{
                            "id.keyword":_id
                        }
                    }
                }         
            else: # 自己的数据，基于allimage字段精准查询
                body = {
                'query': {
                    'match_phrase': {
                        'allimage':img_name   # 使用正则表达式查询
                        }
                    }
                }

            info_org = es_db.search(index='fwnews',body=body)
            try:
                info_dst = info_org.get('hits').get('hits')[0].get('_source')
            except:
                print('ex search error')
                return -1, [], []
            img_url = None
            id_title = info_dst.get('id')
            all_imgs = info_dst.get('allimage')
            title_url = info_dst.get('source_url')
            web_source = info_dst.get('source')
            title = info_dst.get('title')
            img_similar_score = similar_scores[img_name_index]
        similar_infos.append({'img_url':img_url, 'title':title, 'title_url':title_url, 'web_source':web_source, 'img_similar_score':img_similar_score, 'id_title':id_title, 'all_imgs':all_imgs})
    if len(similar_scores) == 0:
        return 1, similar_infos, 0
    else:
        return 1, similar_infos, max(similar_scores)

# 链接es数据库
es_db = Elasticsearch(["192.168.132.152"], http_auth=('elastic', 'Ynwy778123'), port=9200)

app = Flask(__name__)

@app.route("/imgsimilar",methods = ['GET', 'POST'])
def get_similar_img():
    if request.method == "POST":
        # 初始化最大相似度
        sign = -1 # 有效标识位
        similar_value_max = 0 # 最大相似度
        similar_infos = [] # 相似度高于阈值的图像列表，格式如[{img1},{img2},{img3}...]
        # 获取图像base64数据
        temp_img_base64 = request.form.get('imgbase64')
        temp_img_base64 = re.sub(r'data:image/[a-zA-Z]*;base64,', "",temp_img_base64) # 适配js库base64
        temp_img_base64 = temp_img_base64.replace("data:image/jpeg;base64,", "") # 适配多种图像类型
        limit = request.form.get('limit')
        name_unique = request.form.get('unique_str')
        temp_img_base64 = base64.b64decode(temp_img_base64)
        rand_img_name = getRandomSet(20)+ '@#$!!' + name_unique + '.jpg'
        temp_img_path = os.path.join('temp', rand_img_name)
        file = open(temp_img_path,'wb')
        file.write(temp_img_base64)
        file.close()
        #try:
        sign,similar_infos, similar_value_max = get_limit_imgpath(temp_img_path, limit)
        os.remove(temp_img_path)
        if sign == -1:
            return json.dumps({'sign':sign, 'similar_value_max':similar_value_max, 'similar_infos':similar_infos})
        if len(similar_infos) > 0: # 存在相似图像
            sign = 1
            return json.dumps({'sign':sign, 'similar_value_max':similar_value_max, 'similar_infos':similar_infos})
        else: # 不存在相似图像
            sign = 0
            return json.dumps({'sign':sign, 'similar_value_max':similar_value_max, 'similar_infos':similar_infos})
        #except:
        #    return json.dumps({'sign':sign, 'similar_value_max':similar_value_max, 'similar_infos':similar_infos})
    else:
        return "<h1>match img, please use post !</h1>"

if __name__ == "__main__":
    host = '0.0.0.0'
    port = '8088'
    app.run(debug=True, host=host, port=port, threaded=True)
