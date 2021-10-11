import re

def isNumber(num):
  pattern = r'^[-+]?[-0-9]\d*\.\d*|[-+]?\.?[0-9]\d*$'
  result = re.match(pattern, num)
  return result
