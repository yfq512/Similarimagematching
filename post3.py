#coding=utf-8
import requests
import time
import base64

t1 = time.time()
s = requests
data={'delname':'于国安.jpg'}
r = s.post('http://0.0.0.0:8082/delimgs', data)

print(r.text)
print('time cost:', time.time() - t1)
