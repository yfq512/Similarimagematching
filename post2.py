#coding=utf-8
import requests
import time
import base64

t1 = time.time()
s = requests
with open('1.jpg', 'rb') as f:
    imgbase64 = base64.b64encode(f.read())
data={'imgbase64':imgbase64}
r = s.post('http://0.0.0.0:8082/updataimgs', data)

print(r.text)
print('time cost:', time.time() - t1)
