import requests
from requests.exceptions import ReadTimeout
import json
import re
from CMD import CN_CODE_TYPE
import util

def query(codeDic, scheduler = False):
    
    fundList = []
    AShareList = []
    HShareList = []
    ETFList = []
    for code, ctype in codeDic.items():
        if ctype == 'fu':
            fundList.append(code)
        elif ctype == 'cn':
            AShareList.append(code)
        elif ctype == 'hk':
            HShareList.append(code)
        elif ctype == 'etf':
            ETFList.append(code)
    fundResult = ""
    aShareResult = ""
    ETFResult = ""
    hShareResult = ""
    if scheduler:
        if util.getAShareStatus():
            fundResult = queryFund(fundList)
            aShareResult = queryAShares(AShareList)
            ETFResult = queryETF(ETFList)
        if util.getHShareStatus():
            hShareResult = queryHShares(HShareList)
    else:
        fundResult = queryFund(fundList)
        aShareResult = queryAShares(AShareList)
        hShareResult = queryHShares(HShareList)
        ETFResult = queryETF(ETFList)
    reply_text = fundResult + aShareResult + hShareResult + ETFResult
    return reply_text


def queryFund(fundList):
    # 查询基金，使用天天基金接口
    if len(fundList) == 0:
        return ""
    reply_text = ""
    for fund in fundList:
        if len(str(fund.strip())) != 6:
            tmp ="基金代码为6位，请检查".format(str(fund.strip()))
        else:
            try:
                res = requests.get("http://fundgz.1234567.com.cn/js/{}.js".format(fund.strip()),timeout=5)
            except ReadTimeout as e:
                tmp = "基金代码: {}, 查询超时，请稍后再试".format(str(fund.strip()))
                continue
            # 正则表达式
            pattern = r'^jsonpgz\((.*)\)'
            # 查找结果
            fundsearch = re.findall(pattern, res.text)
            if len(fundsearch) == 0 or len(fundsearch[0]) == 0:
                tmp = "不存在该基金代码：{}".format(fund.strip())
            # 遍历结果
            else:
                for fundItem in fundsearch:
                    data = json.loads(fundItem)
                    tmp = "基金代码: {}, 基金: {}, 当前净值: {},涨跌: {}%,更新时间: {}".format(data['fundcode'], data['name'], data['gsz'],data['gszzl'], data['gztime'])
    
        reply_text = reply_text + "\n\n" + tmp

    return reply_text

def queryAShares(AShareList):
    if len(AShareList) == 0:
        return ""
    reply_text = ""
    for ashare in AShareList:
        if len(str(ashare.strip())) != 6:
            tmp ="A股代码为6位，请检查".format(str(ashare.strip()))
        else:
            if ashare[0:2] in CN_CODE_TYPE:
                ashare_code = CN_CODE_TYPE[ashare[0:2]] + ashare
            elif ashare[0:3] in CN_CODE_TYPE:
                ashare_code = CN_CODE_TYPE[ashare[0:3]] + ashare
            else:
                reply_text = reply_text + "该代码不存在或暂不支持该代码\n"
                continue
            try:
                res = requests.get("https://hq.sinajs.cn/list={}".format(ashare_code.strip()),timeout=5)
            except ReadTimeout as e:
                tmp = "股票代码: {}, 查询超时，请稍后再试".format(str(ashare.strip()))
                continue
            if res.status_code == 200:
                aShareSearch = res.text.split("\"")[1]
            else:
                tmp = "股票代码: {}, 查询错误，请稍后再试".format(str(ashare.strip()))
                continue
            if len(aShareSearch) == 0:
                tmp = "不存在该股票代码：{}".format(ashare.strip())
            # 遍历结果
            else:
                # 名称
                shareName = aShareSearch.split(',')[0]
                # 昨收
                shareLastDayPrice = float(aShareSearch.split(',')[2])
                # 实时价格
                shareNowPrice = float(aShareSearch.split(',')[3])
                # 涨跌
                rate = round((shareNowPrice - shareLastDayPrice)/shareLastDayPrice*100,2)
                # 时间
                priceTime = aShareSearch.split(',')[30] + " " + aShareSearch.split(',')[31]

                tmp = "股票代码: {}, 股票名称：{}, 实时价格: {},涨跌: {}%,更新时间: {}".format(ashare, shareName, shareNowPrice, rate, priceTime)
    
        reply_text = reply_text + "\n\n" + tmp

    return reply_text

def queryHShares(HShareList):
    if len(HShareList) == 0:
        return ""
    reply_text = ""
    for hshare in HShareList:
        if len(str(hshare.strip())) != 5:
            tmp ="港股代码为5位，请检查".format(str(hshare.strip()))
        else:
            hshare_code = 'hk' + hshare
            try:
                res = requests.get("https://hq.sinajs.cn/list={}".format(hshare_code.strip()),timeout=5)
            except ReadTimeout as e:
                tmp = "股票代码: {}, 查询超时，请稍后再试".format(str(hshare.strip()))
                continue
            if res.status_code == 200:
                hShareSearch = res.text.split("\"")[1]
            else:
                tmp = "股票代码: {}, 查询错误，请稍后再试".format(str(hshare.strip()))
                continue
            if len(hShareSearch) == 0:
                tmp = "不存在该股票代码：{}".format(hshare.strip())
            # 遍历结果
            else:
                # 名称
                shareName = hShareSearch.split(',')[1]
                # 昨收
                shareLastDayPrice = float(hShareSearch.split(',')[3])
                # 实时价格
                shareNowPrice = float(hShareSearch.split(',')[6])
                # 涨跌
                rate = round((shareNowPrice - shareLastDayPrice)/shareLastDayPrice*100,2)
                # 时间
                priceTime = hShareSearch.split(',')[-2].replace('/','-') + " " + hShareSearch.split(',')[-1]

                tmp = "股票代码: {}, 股票名称：{}, 实时价格: {},涨跌: {}%,更新时间: {}".format(hshare, shareName, shareNowPrice, rate, priceTime)
    
        reply_text = reply_text + "\n\n" + tmp

    return reply_text

def queryETF(ETFList):
    if len(ETFList) == 0:
        return ""
    reply_text = ""
    for etf in ETFList:
        if len(str(etf.strip())) != 6:
            tmp ="场外ETF代码为6位，请检查".format(str(etf.strip()))
        else:
            # 对于场外ETF，一些QDII基金无实时信息，接口请求时查询f_code;
            # 而其他场外ETF，有实时信息，接口请求时查询fu_code;
            # 因此，先查询fu_code，如无结果，再查询f_code；
            etf_code = 'fu_' + etf
            try:
                res = requests.get("https://hq.sinajs.cn/list={}".format(etf_code.strip()),timeout=5)
            except ReadTimeout as e:
                tmp = "ETF代码: {}, 查询超时，请稍后再试".format(str(etf.strip()))
                continue
            etfSearch = []
            if res.status_code == 200:
                etfSearch = res.text.split("\"")[1]
                if len(etfSearch) == 0:
                    etf_code = 'f_' + etf
                    try:
                        res = requests.get("https://hq.sinajs.cn/list={}".format(etf_code.strip()),timeout=5)
                    except ReadTimeout as e:
                        tmp = "ETF代码: {}, 查询超时，请稍后再试".format(str(etf.strip()))
                        continue
                    if res.status_code == 200:
                        etfSearch = res.text.split("\"")[1]
                    else:
                        tmp = "ETF代码: {}, 查询错误，请稍后再试".format(str(etf.strip()))
                        continue
            else:
                tmp = "ETF代码: {}, 查询错误，请稍后再试".format(str(etf.strip()))
                continue
            if len(etfSearch) == 0:
                tmp = "不存在该ETF代码：{}".format(etf.strip())
            # 遍历结果
            else:
                # 名称
                etfName = etfSearch.split(',')[0]
                # 时间
                if etf_code[0:2] == "f_":
                    # 对于QDII，不计算实时净值和涨跌
                    # 最新净值
                    etfNowPrice = float(etfSearch.split(',')[1])
                    priceTime = etfSearch.split(',')[-2]
                    tmp = "ETF代码: {}, ETF名称：{}, 最新净值: {}, 更新时间: {}".format(etf, etfName, etfNowPrice, priceTime)
                else:
                    etf_code = "fu_" + etf
                    # 其他ETF计算实时净值和涨跌
                    # 昨收
                    etfLastDayPrice = float(etfSearch.split(',')[3])
                    # 实时价格
                    etfNowPrice = float(etfSearch.split(',')[2])
                    # 涨跌
                    rate = round((etfNowPrice - etfLastDayPrice)/etfLastDayPrice*100,2)
                    priceTime = etfSearch.split(',')[-1] + etfSearch.split(',')[1]
                    tmp = "ETF代码: {}, ETF名称：{}, 当前净值: {},涨跌: {}%,更新时间: {}".format(etf, etfName, etfNowPrice, rate, priceTime)

        reply_text = reply_text + "\n\n" + tmp

    return reply_text

def queryName(codeDic):
    result = []
    for code, ctype in codeDic.items():
        if ctype == 'fu':
            try:
                res = requests.get("http://fundgz.1234567.com.cn/js/{}.js".format(code.strip()),timeout=5)
            except ReadTimeout as e:
                tmp = {code:{"isOk":False, "fundName":"", "fundType":ctype, "comment":"请求超时"}}
                continue
            fundsearch = []
            if res.status_code == 200:
                # 正则表达式
                pattern = r'^jsonpgz\((.*)\)'
                # 查找结果
                fundsearch = re.findall(pattern, res.text)
            else:
                tmp = {code:{"isOk":False, "fundName":"", "fundType":ctype, "comment":"请求错误"}}

            if len(fundsearch) == 0 or len(fundsearch[0]) == 0:
                tmp = {code:{"isOk":False, "fundName":"", "fundType":ctype, "comment":"该代码不存在"}}
            # 遍历结果
            else:
                for fundItem in fundsearch:
                    data = json.loads(fundItem)
                tmp = {code:{"isOk":True, "fundName":data['name'], "fundType":ctype, "comment":""}}

        elif ctype == 'cn':
            ashare_code = CN_CODE_TYPE[code[0:3]] + code
            try:
                res = requests.get("https://hq.sinajs.cn/list={}".format(ashare_code.strip()),timeout=5)
            except ReadTimeout as e:
                tmp = {code:{"isOk":False, "fundName":"", "fundType":ctype, "comment":"请求超时"}}
                continue
            aShareSearch = []
            if res.status_code == 200:
                aShareSearch = res.text.split("\"")[1]
            else:
                tmp = {code:{"isOk":False, "fundName":"", "fundType":ctype, "comment":"请求错误"}}
                continue
            if len(aShareSearch) == 0:
                tmp = {code:{"isOk":False, "fundName":"", "fundType":ctype, "comment":"该代码不存在"}}
            else:
                tmp = {code:{"isOk":True, "fundName":aShareSearch.split(',')[0], "fundType":ctype, "comment":""}}

        elif ctype == 'hk':                
            hshare_code = 'hk' + code
            try:
                res = requests.get("https://hq.sinajs.cn/list={}".format(hshare_code.strip()),timeout=5)
            except ReadTimeout as e:
                tmp = {code:{"isOk":False, "fundName":"", "fundType":ctype, "comment":"请求超时"}}
                continue
            hShareSearch = []
            if res.status_code == 200:
                hShareSearch = res.text.split("\"")[1]
            else:
                tmp = {code:{"isOk":False, "fundName":"", "fundType":ctype, "comment":"请求错误"}}
                continue
            if len(hShareSearch) == 0:
                tmp = {code:{"isOk":False, "fundName":"", "fundType":ctype, "comment":"该代码不存在"}}
            else:
                tmp = {code:{"isOk":True, "fundName":hShareSearch.split(',')[1], "fundType":ctype, "comment":""}}

        elif ctype == 'etf':                
            etf_code = 'f_' + code
            try:
                res = requests.get("https://hq.sinajs.cn/list={}".format(etf_code.strip()),timeout=5)
            except ReadTimeout as e:
                tmp = {code:{"isOk":False, "fundName":"", "fundType":ctype, "comment":"请求超时"}}
                continue
            etfSearch = []
            if res.status_code == 200:
                etfSearch = res.text.split("\"")[1]
            else:
                tmp = {code:{"isOk":False, "fundName":"", "fundType":ctype, "comment":"请求错误"}}
                continue
            if len(etfSearch) == 0:
                tmp = {code:{"isOk":False, "fundName":"", "fundType":ctype, "comment":"该代码不存在"}}
            else:
                tmp = {code:{"isOk":True, "fundName":etfSearch.split(',')[0], "fundType":ctype, "comment":""}}
        
        result.append(tmp)
        
    return result