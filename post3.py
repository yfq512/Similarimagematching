#coding=utf-8
import requests
import time
import base64

t1 = time.time()
s = requests
data={'delname':'9pcdtm01f5g7jzrh8lu6.jpg'}
r = s.post('http://192.168.132.151:8088/delimgs', data)

print(r.text)
print('time cost:', time.time() - t1)
