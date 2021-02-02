from kafka import KafkaConsumer, TopicPartition
import time
import json
import os
from init_load_img2npy2 import auto_updata_imgnpy as load_imgnpy # 使用优化后的数据插入，不得重复掺入

def compare_time(t1, t2): # such as '2021-01-11 14:27:00', if t2>=t1 return True, or return Flase
    t1_year = int(t1.split(' ')[0].split('-')[0])
    t1_month = int(t1.split(' ')[0].split('-')[1])
    t1_day = int(t1.split(' ')[0].split('-')[2])
    t1_hour = int(t1.split(' ')[1].split(':')[0])
    t1_min = int(t1.split(' ')[1].split(':')[1])
    t1_s = int(t1.split(' ')[1].split(':')[2])
    
    t2_year = int(t2.split(' ')[0].split('-')[0])
    t2_month = int(t2.split(' ')[0].split('-')[1])
    t2_day = int(t2.split(' ')[0].split('-')[2])
    t2_hour = int(t2.split(' ')[1].split(':')[0])
    t2_min = int(t2.split(' ')[1].split(':')[1])
    t2_s = int(t2.split(' ')[1].split(':')[2])
    
    if t1_year > t2_year:
        return False
    elif t1_month > t2_month:
        return False
    elif t1_day > t2_day:
        return False
    elif t1_hour > t2_hour:
        return False
    elif t1_min > t2_min:
        return False
    elif t1_s > t2_s:
        return False
    else:
        return True

def get_imgpath(imgurl_list, root_ = '/cmdata/'):
    imgpath_list = []
    for n in imgurl_list:
        n_split = n.split('https://filefusion.ccwb.cn/')
        imgpath = os.path.join(root_, n_split[1])
        imgpath_list.append(imgpath)
    return imgpath_list
    
if __name__ == "__main__":
    consumer = KafkaConsumer(bootstrap_servers=['192.168.132.111:9092'], group_id='image_proccess')
    consumer.assign([
        TopicPartition(topic="example", partition=0)
    ])
    consumer.seek(TopicPartition(topic="example", partition=0), 0)
    
    last_time = '2021-01-11 14:27:00'
    cnt3 = 0
    for msg in consumer:
        with open('kafka.log','a') as f4:
            f4.write(str(cnt3))
            f4.write('\n')
            f4.close()
            cnt3 = cnt3 + 1
        info = json.loads(msg.value)
        info2 = info.get('data')[0]
        create_time = info2.get('create_time')
        if create_time == None:
            with open('log_nocreat_time.log', 'a') as f:
                f.write(str(info2))
                f.write('\n')
                f.close()
            continue
        # print(create_time, type(allimage_list), allimage_list)
        if compare_time(last_time, create_time):
            allimage = info2.get('allimage')
            allimage_list = allimage.split(';')
            if allimage_list[0] == '':
                continue
            imgpath_list = get_imgpath(allimage_list)
            for n in imgpath_list:
                #creat_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.stat(n).st_ctime))
                now_time = time.strftime("%F %H:%M:%S")
                with open('auto_load_mydata.log','a') as f3:
                    f3.write(now_time+';'+n)
                    f3.write('\n')
                    f3.close()
                sign = load_imgnpy(n)
