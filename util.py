from os import stat
import re
import requests
import json

def isNumber(num):
  pattern = r'^[-+]?[-0-9]\d*\.\d*|[-+]?\.?[0-9]\d*$'
  result = re.match(pattern, num)
  return result

def getAShareStatus():
  status = 0
  try:
    res = requests.get("https://push2.eastmoney.com/api/qt/stock/get?secid=1.000001&fields=f118,f57", timeout=5)
  except :
    return False
  if res.status_code == 200:
    status = int(json.loads(res.text)['data']['f118'])
  else:
    return False
  
  if status in [1,2,4]:
    return True
  else:
    return False

def getHShareStatus():
  status = 0
  try:
    res = requests.get("https://push2.eastmoney.com/api/qt/stock/get?secid=100.HSI&fields=f118,f57", timeout=5)
  except :
    return False
  if res.status_code == 200:
    status = int(json.loads(res.text)['data']['f118'])
  else:
    return False
  
  if status in [1,2,4]:
    return True
  else:
    return False
