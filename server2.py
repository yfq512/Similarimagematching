import cv2, os, time, random, base64, shutil, fcntl, re, json
from fun_base import fun_Hash, com2hashstr
from flask import Flask,render_template,request
from elasticsearch import Elasticsearch

def getRandomSet(bits):
    num_set = [chr(i) for i in range(48,58)]
    char_set = [chr(i) for i in range(97,123)]
    total_set = num_set + char_set
    value_set = "".join(random.sample(total_set, bits))
    return value_set

def load_img(orgimgroot):
    hash_str_list = []
    imgpath_list = []
    orgimg_list = os.listdir(orgimgroot)
    cnt = 0
    cnt_error = 0
    for n in orgimg_list:
        imgpath = os.path.join(orgimgroot, n)
        print('>>>',cnt, imgpath)
        cnt = cnt + 1
        try:
            img = cv2.imread(imgpath)
            img.shape
        except:
            print('read img error: ', imgpath)
            cnt_error = cnt_error + 1
            continue
        img_hash = fun_Hash(img)
        hash_str_list.append(img_hash)
        # 拼接es数据库图像url，接下来仍然需要调整的 ！！！！！！！！！！
        imgpath = ["allimage","https://filefusion.ccwb.cn/files/2020/12/images/" + n]
        imgpath_list.append(imgpath)
    print('successful and error: ',cnt, cnt_error)
    return hash_str_list, imgpath_list

def upimgs(upimgroot, orgimgroot):
    _hash_strs = []
    _imgpaths = []
    upimg_list = os.listdir(upimgroot)
    for n in upimg_list:
        imgpath = os.path.join(upimgroot, n)
        copy_path = os.path.join(orgimgroot, n)
        shutil.copyfile(imgpath, copy_path)
        os.remove(imgpath)
        try:
            img = cv2.imread(copy_path)
        except:
            print('read img error:', copy_path)
            img = None
        img_hash = fun_Hash(img)
        _hash_strs.append(img_hash)
        _imgpaths.append(copy_path)
        print('adding: ', copy_path)
    return _hash_strs, _imgpaths

def get_limit_imgpath(dstimgpath, _hash_strs, _imgpaths, limit):
    limit = int(limit)
    dstimg = cv2.imread(dstimgpath)
    dstimg_2 = cv2.flip(dstimg, 1) # check overturn image on the same time
    dst_hash_str = fun_Hash(dstimg)
    dst_hash_str_2 = fun_Hash(dstimg_2)
    out_imgpaths = []
    similar_scores = []
    for n in range(len(_hash_strs)):
        temp_value = com2hashstr(dst_hash_str, _hash_strs[n])
        temp_value_2 = com2hashstr(dst_hash_str_2, _hash_strs[n])
        temp_value = max(temp_value, temp_value_2) # use max score
        if temp_value > limit:
            out_imgpaths.append(_imgpaths[n])
            similar_scores.append(temp_value)
            
    # 查询es数据库，返回similar_infos
    similar_infos = []
    for id in range(len(out_imgpaths)):
        id_img_str = out_imgpaths[id]
        str1 = id_img_str[0]
        str2 = id_img_str[1]
        # 根据图像URL（视为唯一id），模糊匹配title，在解析title信息
        print('==========',str2)
        body = {
            "query":{
                "match":{
                    str1:str2
                }
            }
        }
        info_org = es_db.search(index='fwnews',body=body)
        info_dst = info_org.get('hits').get('hits')[0].get('_source')
        img_url = str2
        id_title = info_dst.get('id')
        all_imgs = info_dst.get('allimage')
        title_url = info_dst.get('source_url')
        web_source = info_dst.get('source')
        title = info_dst.get('title')
        img_similar_score = similar_scores[id]
        similar_infos.append({'img_url':img_url, 'title':title, 'title_url':title_url, 'web_source':web_source, 'img_similar_score':img_similar_score, 'id_title':id_title, 'all_imgs':all_imgs})
    if len(similar_scores) == 0:
        return similar_infos, 0
    else:
        return similar_infos, max(similar_scores)

def get_list_index(org_list, new_list):
    nums_list = []
    cnt = 0
    for n in org_list:
        if n in new_list:
            nums_list.append(cnt)
        cnt = cnt + 1
    return nums_list

def delimg_online(orgimgroot, delimgsign_path, hash_strs, imgpaths):
    delimglist = []
    for n in open(delimgsign_path):
        delimglist.append(os.path.join(orgimgroot,n[:-1]))
    numslist = get_list_index(imgpaths, delimglist)
    print('dasdsdasdasdsadasdsadsaasdas', imgpaths, numslist)
    for index_ in numslist:
        del hash_strs[index_]
        del imgpaths[index_]
    return hash_strs, imgpaths

orgimgroot = 'orgimgs_from_es'
upimgroot = 'uporgimgs'
upimgsign_path = 'upimgsign.txt'
delimgsign_path = 'delimg.txt'

# 链接es数据库
es_db = Elasticsearch(["192.168.132.152"], http_auth=('elastic', 'Ynwy778123'), port=9200)

app = Flask(__name__)
hash_strs, imgpaths = load_img(orgimgroot)

@app.route("/imgsimilar",methods = ['GET', 'POST'])
def get_similar_img():
    if request.method == "POST":
        if os.path.exists(upimgsign_path):
            new_hash_strs, new_imgpaths = upimgs(upimgroot, orgimgroot)
            os.remove(upimgsign_path)
            for n in new_hash_strs:
                hash_strs.append(n)
            for m in new_imgpaths:
                imgpaths.append(m)
        if os.path.exists(delimgsign_path):
            delimg_online(orgimgroot, delimgsign_path, hash_strs, imgpaths)
            os.remove(delimgsign_path)
        
        # 初始化最大相似度
        sign = -1 # 有效标识位
        similar_value_max = 0 # 最大相似度
        similar_infos = [] # 相似度高于阈值的图像列表，格式如[{img1},{img2},{img3}...]
        
        # print(imgpaths)
        # 获取图像base64数据
        temp_img_base64 = request.form.get('imgbase64')
        temp_img_base64 = re.sub(r'data:image/[a-zA-Z]*;base64,', "",temp_img_base64) # 适配js库base64
        temp_img_base64 = temp_img_base64.replace("data:image/jpeg;base64,", "") # 适配多种图像类型
        limit = request.form.get('limit')
        temp_img_base64 = base64.b64decode(temp_img_base64)
        rand_img_name = getRandomSet(20) + '.jpg'
        temp_img_path = os.path.join('temp', rand_img_name)
        file = open(temp_img_path,'wb')
        file.write(temp_img_base64)
        file.close()
        #try:
        similar_infos, similar_value_max = get_limit_imgpath(temp_img_path, hash_strs, imgpaths, limit)
        os.remove(temp_img_path)
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

@app.route("/updataimgs",methods = ['GET', 'POST'])
def updataimgs():
    if request.method == "POST":
        sign_Mandatory_add = request.form.get('sign_add')
        imgbase64 = request.form.get('imgbase64')
        imgbase64 = base64.b64decode(imgbase64)
        randname = getRandomSet(20) + '.jpg'
        imgpath = os.path.join(upimgroot ,randname)
        file = open(imgpath,'wb')
        file.write(imgbase64)
        file.close()
        if sign_Mandatory_add == '1':
            if not os.path.exists(upimgsign_path):
                with open(upimgsign_path,'w') as f:
                    f.write('sign')
                    f.close()
            return {'sign':1, 'savename':randname}
        uplimit_imgpaths = get_limit_imgpath(imgpath, hash_strs, imgpaths)
        if not len(uplimit_imgpaths) == 0:
            os.remove(imgpath)
            return {'sign':-1, 'savename':uplimit_imgpaths} # add img similar up limit ,return similar up orgimgpath_list

        if not os.path.exists(upimgsign_path):
            with open(upimgsign_path,'w') as f:
                f.write('sign')
                f.close()
        return {'sign':1, 'savename':randname} # add scuessful, return name in orgdata
    else:
        return "<h1>Updata img, please use post !</h1>"

@app.route("/delimgs",methods = ['GET', 'POST'])
def _delimgs():
    if request.method == "POST":
        delname = request.form.get('delname')
        orgimg_list = os.listdir(orgimgroot)
        if not delname in orgimg_list:
            return {'sign':-1, 'text':orgimg_list} # failed,return orgimg_list
        with open(delimgsign_path,'a') as f:
            fcntl.flock(f,fcntl.LOCK_EX)
            f.write(delname)
            f.write('\n')
            fcntl.flock(f,fcntl.LOCK_UN)
            f.close()
        os.remove(os.path.join(orgimgroot, delname))
        return {'sign':0, 'text':None} # del scuess
    else:
        return "<h1>Delete img, please use post !</h1>"

@app.route("/com2imgs",methods = ['GET', 'POST'])
def com2imgs():
    if request.method == "POST":
        imgbase64_1 = request.form.get('imgbase64_1')
        imgbase64_1 = base64.b64decode(imgbase64_1)
        imgbase64_2 = request.form.get('imgbase64_2')
        imgbase64_2 = base64.b64decode(imgbase64_2)
        randname1 = getRandomSet(20) + '.jpg'
        randname2 = getRandomSet(20) + '.jpg'
        file = open(randname1,'wb')
        file.write(imgbase64_1)
        file.close()
        file = open(randname2,'wb')
        file.write(imgbase64_2)
        file.close()
        try:
            img1 = cv2.imread(randname1)
            img2 = cv2.imread(randname2)
            hash1 = fun_Hash(img1)
            hash2 = fun_Hash(img2)
            score = com2hashstr(hash1, hash2)
            os.remove(randname1)
            os.remove(randname2)
            return {'sign':1, 'score':score}
        except:
            os.remove(randname1)
            os.remove(randname2)
            return {'sign':-1, 'score':None}
    else:
        return "<h1>compare img, please use post !</h1>"

if __name__ == "__main__":
    host = '0.0.0.0'
    port = '8088'
    app.run(debug=True, host=host, port=port, threaded=True)
