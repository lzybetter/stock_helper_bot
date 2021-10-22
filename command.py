import save
import query
import CMD
import util

def queryAll(chat_id, scheduler = False):
    lines = save.queryDB(chat_id, needColumnsList=['fundCode', 'type'], condition={"isWatch": 1})
    reply_text = ""
    if len(lines) == 0:
        reply_text = "目前没有记录，请先建立记录"
    else:
        codeDict = {}
        for line in lines:
            codeDict[line[0]] = line[1]
        reply_text = query.query(codeDict, scheduler)
    
    return reply_text

def queryCode(query_text):
    reply_text = ""
    code_type = 'fu'
    codeDict = {}
    for t in query_text:
        if t in CMD.CODE_TYPE:
            code_type = t
        else:
            if not util.isNumber(t):
                reply_text = reply_text + "代码必须应为数字：" + t + "\n"
            elif code_type == 'hk' and len(t.strip()) != 5:
                reply_text = reply_text + "港股代码应为5位: " + t + "\n"
            elif code_type == 'cn' and len(t.strip()) != 6:
                reply_text = reply_text + "A股代码应为6位: " + t + "\n"
            elif code_type == 'etf' and len(t.strip()) != 6:
                reply_text = reply_text + "ETF代码应为6位: " + t + "\n"
            elif code_type == 'fu' and len(t.strip()) != 6:
                reply_text = reply_text + "基金代码应为6位: " + t + "\n"
            else:
                codeDict[t] = code_type
    if len(codeDict) == 0:
        reply_text = "请输入需要查询的有效的代码"
    else:
        tmp = query.query(codeDict)
        reply_text = reply_text + tmp

    return reply_text

def saveRecord(chat_id, save_text):
    reply_text = ""
    code_type = 'fu'
    codeDict = {}
    for t in save_text:
        if t in CMD.CODE_TYPE:
            code_type = t
        else:
            if not util.isNumber(t):
                reply_text = reply_text + "代码必须应为数字：" + t + "\n"
            elif code_type == 'hk' and len(t.strip()) != 5:
                reply_text = reply_text + "港股代码应为5位: " + t + "\n"
            elif code_type == 'cn' and len(t.strip()) != 6:
                reply_text = reply_text + "A股代码应为6位: " + t + "\n"
            elif code_type == 'etf' and len(t.strip()) != 6:
                reply_text = reply_text + "ETF代码应为6位: " + t + "\n"
            elif code_type == 'fu' and len(t.strip()) != 6:
                reply_text = reply_text + "基金代码应为6位: " + t + "\n"
            else:
                lines = save.queryDB(chat_id, fundCodeList=[t], needColumnsList=["fundCode"])
                if len(lines) > 0:
                    reply_text = reply_text + "已有该记录： " + t + '\n'
                else:
                    codeDict[t] = code_type
        
    if len(codeDict) == 0:
        reply_text = reply_text + "请输入需要记录的有效的代码"
    else:
        queryResult = query.queryName(codeDict)
        saveDict = {}
        for r in queryResult:
            code, name = list(r.items())[0]
            if name['isOk']:
                saveDict[code] = {"fundName":name["fundName"], "fundType": name['fundType']}
            else:
                if name['comment'] == "该代码不存在":
                    reply_text = reply_text + "该代码不存在： " + code + "\n"
                else:
                    reply_text = reply_text + "%s：名称请求错误，代码已记录，但请更新名称\n".format(code)
                    saveDict[code] = {"fundName":"未知", "fundType": name['fundType']}
        reply_text = reply_text + save.saveNewRecord(chat_id, saveDict)
    
    return reply_text
    
def deleteRecord(chat_id, delete_text):
    reply_text = ""
    fundCodeList = []
    for t in delete_text:
        if not util.isNumber(t):
            reply_text = reply_text + "代码必须应为数字：" + t + "\n"
        else:
            lines = save.queryDB(chat_id, fundCodeList=[t], needColumnsList=["fundCode"])
            if len(lines) == 0:
                reply_text = reply_text + "没有该记录： " + t + '\n'
            else:
                fundCodeList.append(t)
    if len(fundCodeList) == 0:
        reply_text = reply_text + "请输入需要删除的有效的代码"
    else:
        reply_text = reply_text + save.deleteRecord(chat_id, fundCodeList)
    
    return reply_text

def deleteAll(chat_id):
    return save.deleteAllRecord(chat_id)

def listRecord(chat_id):
    reply_text = ""
    lines = save.queryDB(chat_id, needColumnsList=['fundCode', "fundName", 'type', "isHold", "isWatch", "cost_price", "amount"])
    if len(lines) == 0:
        reply_text = "目前没有记录，请先建立记录"
    else:
        for line in lines:
            if line[4] == 0:
                isWatch = "否"
            else:
                isWatch = "是"
            if line[3] == 0:
                isHold = "否"
                tmp = "基金代码：%s，基金名称：%s, 基金类型：%s，是否持有：%s，是否关注：%s \n"\
                    %(line[0], line[1], line[2], isHold, isWatch)
            else:
                isHold = "是"
                tmp = "基金代码：%s，基金名称：%s, 基金类型：%s，是否持有：%s, 成本价：%.2f, 持有份额：%.2f，是否关注：%s \n"\
                    %(line[0], line[1], line[2], isHold, line[5], line[6], isWatch)
            reply_text = reply_text + tmp
    
    return reply_text

def changeName(chat_id, change_text):

    reply_text = ""
    num = len(change_text)
    change_text = []
    if num%2 != 0:
        reply_text = "每个代码只能对应一个名字"
    else:
        num = int(num / 2) - 1
        for i in range(0, num, 2):
            code = change_text[i]
            changeName = change_text[i+2]
            change_text.append({code:changeName})

        reply_text = reply_text + save.changeName(chat_id, change_text)
    
    return reply_text

def buyRecord(chat_id, buy_text):
    reply_text = ""
    next_text = "type"
    code_type = "fu"
    code = ""
    price = 0
    amount = 0
    saveDict = []
    for t in buy_text:
        if next_text == "type":
            if t in CMD.CODE_TYPE:
                code_type = t
            elif util.isNumber(t) and len(t.strip()) in (5, 6):
                code_type = code_type
            else:
                reply_text = reply_text + "无法识别的类型: " + t + "\n"
                code_type = ""
            next_text = "code"
        elif next_text == "code":
            code = ""
            if not util.isNumber(t):
                reply_text = reply_text + "代码必须应为数字：" + t + "\n"
            elif code_type == 'hk' and len(t.strip()) != 5:
                reply_text = reply_text + "港股代码应为5位: " + t + "\n"
            elif code_type == 'cn' and len(t.strip()) != 6:
                reply_text = reply_text + "A股代码应为6位: " + t + "\n"
            elif code_type == 'etf' and len(t.strip()) != 6:
                reply_text = reply_text + "ETF代码应为6位: " + t + "\n"
            elif code_type == 'fu' and len(t.strip()) != 6:
                reply_text = reply_text + "基金代码应为6位: " + t + "\n"
            else:
                code = t
            next_text = "price"
        elif next_text == "price":
            if not util.isNumber(t) or float(t) <= 0:
                reply_text = reply_text + "单价必须应为数字, 且必须为正数：" + t + "\n"
                price = 0
            else:
                price = float(t)
            next_text = "amount"
        elif next_text == "amount":
            if not util.isNumber(t) or float(t) <= 0:
                reply_text = reply_text + "份数必须应为数字, 且必须为正数：" + t + "\n"
                amount = 0
            else:
                amount = float(t)
            next_text = "type"
            if code_type != "" and code != "" and price > 0 and amount > 0:
                saveDict.append({code:{"cost_price":price, "amount":amount, "type": code_type}})
    if len(saveDict) > 0:
        reply_text = reply_text + save.buyRecord(chat_id, saveDict)
    else:
        reply_text = reply_text + "请输入有效的购买记录"
    return reply_text

def sellRecord(chat_id, sell_text):
    reply_text = ""
    next_text = "code"
    code = ""
    price = 0
    amount = 0
    now_amount = 0
    sellDict = []
    isAll = False
    for t in sell_text:
        if next_text == "code":
            code = ""
            if not util.isNumber(t):
                reply_text = reply_text + "代码必须为数字：" + t + "\n"
            elif len(t) not in (5,6):
                reply_text = reply_text + "代码必须为5/6位数字：" + t + "\n"
            else:
                code = t
                lines = save.queryDB(chat_id, fundCodeList=[code], needColumnsList=["amount", "isHold"])
                if len(lines) > 0:
                    isHold = lines[0][1]
                    if isHold == 0:
                        reply_text = reply_text + "您未持有该股票：" + t + "\n"
                        code = ""
                    else:
                        now_amount = float(lines[0][0])
                        if now_amount == 0:
                            reply_text = reply_text + "未持有的份数为0，无法卖出：" + t + "\n"
                            code = ""
                else:
                    reply_text = reply_text + "没有该记录：" + t + "\n"
                    code = ""
            next_text = "price"
        elif next_text == "price":
            isAll = False
            next_text = "amount"
            if t == "all" or t == "ALL":
                isAll = True
                price = 0
                amount = 0
                next_text = "code"
                if code != "" and isAll :
                    sellDict.append({code:{"isAll": isAll, "cost_price":price, "amount":amount}})
            elif not util.isNumber(t) or float(t) <= 0:
                reply_text = reply_text + "单价必须应为数字, 且必须为正数：" + t + "\n"
                price = 0
            else:
                price = float(t)
        elif next_text == "amount":
            if not util.isNumber(t) or float(t) <= 0:
                reply_text = reply_text + "份数必须应为数字, 且必须为正数：" + t + "\n"
                amount = 0
            elif amount > now_amount:
                reply_text = reply_text + "卖出份数大于持有份数，请检查：" + t + "\n"
                amount = 0
            else:
                amount = float(t)
            if code != "" and price > 0 and amount > 0 :
                sellDict.append({code:{"isAll": isAll, "cost_price":price, "amount":amount}})
            next_text = "code"
        
    if len(sellDict) > 0:
        reply_text = reply_text + save.sellRecord(chat_id, sellDict)
    else:
        reply_text = reply_text + "请输入卖出的购买记录"
    
    return reply_text

def watchRecord(chat_id, watchList):
    reply_text = ""
    for t in watchList:
        if not util.isNumber(t):
            reply_text = reply_text + "代码必须为数字：" + t + "\n"
        elif len(t) not in (5,6):
            reply_text = reply_text + "代码必须为5/6位数字：" + t + "\n"
        else:
            lines = save.queryDB(chat_id, fundCodeList=[t], needColumnsList=["isWatch"])
            if len(lines) < 1:
                reply_text = reply_text + "未记录该代码，请先记录：%s\n"%t
            else:
                isWatch = lines[0][0]
                if isWatch == 1:
                    reply_text = reply_text + "该代码已关注：%s\n"%t
                else:
                    reply_text = reply_text + save.watchRecord(chat_id, watchList=[t])
    
    return reply_text

def unwatchRecord(chat_id, unwatchList):
    reply_text = ""
    for t in unwatchList:
        if not util.isNumber(t):
            reply_text = reply_text + "代码必须为数字：" + t + "\n"
        elif len(t) not in (5,6):
            reply_text = reply_text + "代码必须为5/6位数字：" + t + "\n"
        else:
            lines = save.queryDB(chat_id, fundCodeList=[t], needColumnsList=["isWatch"])
            if len(lines) < 1:
                reply_text = reply_text + "未记录该代码，请先记录：%s\n"%t
            else:
                isWatch = lines[0][0]
                if isWatch == 0:
                    reply_text = reply_text + "该代码已取消关注：%s\n"%t
                else:
                    reply_text = reply_text + save.unwatchRecord(chat_id, unwatchList=[t])
    
    return reply_text