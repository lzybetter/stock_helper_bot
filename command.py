import save
import query
import CMD
import util

def queryAll(chat_id):
    lines = save.queryDB(chat_id, needColumnsList=['fundCode', 'type'])
    reply_text = ""
    if len(lines) == 0:
        reply_text = "目前没有记录，请先建立记录"
    else:
        codeDict = {}
        for line in lines:
            codeDict[line[0]] = line[1]
        reply_text = query.query(codeDict)
    
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
            elif code_type in ['fu', 'cn'] and len(t.strip()) != 6:
                reply_text = reply_text + "A股/基金代码应为6位: " + t + "\n"
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
        print(t)
        if t in CMD.CODE_TYPE:
            code_type = t
        else:
            if not util.isNumber(t):
                reply_text = reply_text + "代码必须应为数字：" + t + "\n"
            elif code_type == 'hk' and len(t.strip()) != 5:
                reply_text = reply_text + "港股代码应为5位: " + t + "\n"
            elif code_type in ['fu', 'cn'] and len(t.strip()) != 6:
                reply_text = reply_text + "A股/基金代码应为6位: " + t + "\n"
            else:
                lines = save.queryDB(chat_id, fundCodeList=[t], needColumnsList=["fundCode"])
                if len(lines) > 0:
                    reply_text = reply_text + "已有该记录： " + t + '\n'
                else:
                    codeDict[t] = code_type
        
    if len(codeDict) == 0:
        reply_text = "请输入需要记录的有效的代码"
    else:
        queryResult = query.queryName(codeDict)
        saveDict = {}
        for r in queryResult:
            print(list(r.items()))
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
    