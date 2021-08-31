import pymysql
import query
from config import getSqlConfig

def getConn(db=None):
    host, port, user, password = getSqlConfig()
    if db is None:
        conn = pymysql.connect(host=host, port=port, user=user, password=password)
    else:
        conn = pymysql.connect(host=host, port=port, user=user, password=password, db=db)
    return conn

def createTable(chat_id):
    conn = getConn()
    cur = conn.cursor()
    cur.execute('create database if not exists fund_helper')
    cur.execute('use fund_helper')
    cur.execute('create table if not exists %s (id int AUTO_INCREMENT not null COMMENT \'主键\', \
    fundCode VARCHAR(20) not null COMMENT \'基金代码\', \
    fundName VARCHAR(20) default null COMMENT \'基金名称\',\
    type  VARCHAR(20) not null COMMENT \'类型， fu-基金，cn-A股，hk-港股\', \
    isHold int not null COMMENT \'是否持仓\', \
    cost_price float COMMENT \'持仓成本\', \
    total float COMMENT \'持仓总额\', \
    isWatch int not null default 0 COMMENT \'是否关注， 0-不关注，1-关注\', \
    highPrice float COMMENT \'最高价\', \
    highPriceDate VARCHAR(20) COMMENT \'最高价记录时间\', \
    lowPrice float COMMENT \'最低价\', \
    lowPriceDate VARCHAR(20) COMMENT \'最低价记录时间\', \
    PRIMARY KEY (ID)) '%("record_"+chat_id).strip())
    conn.commit()
    cur.close()
    conn.close()

def saveNewRecord(chat_id, newRecords):
    reply_text = ""
    conn = getConn(db='fund_helper')
    cur = conn.cursor()
    save_sql = "insert into %s(fundCode, fundName, type, isHold, isWatch) values "%("record_"+chat_id).strip()
    #字典结构：{"fundCode":{"fundName":"something","fundType":"someting"}}
    for fundCode, record in newRecords.items():
        fundName, fundType = record.items()
        fundName = fundName[1]
        fundType = fundType[1]
        save_sql = save_sql + "(\'%s\', \'%s\', \'%s\', %d, %d), "%(fundCode, fundName, fundType, 0, 1)
    
    save_sql = save_sql[0:-2]
    print(save_sql)

    try:
        cur.execute(save_sql)
        conn.commit()
        reply_text = "存储完毕"
    except:
        reply_text = "存储过程错误，请重试"
    finally:
        cur.close()
        conn.close()
    
    return reply_text

def queryDB(chat_id, fundCodeList=None, needColumnsList=None):

    result = ""
    conn = getConn(db='fund_helper')
    cur = conn.cursor()

    if fundCodeList is None and needColumnsList is None:
        query_sql = "select * from %s"%("record_"+chat_id).strip()
    elif fundCodeList is None:
        query_sql = "select "
        for c in needColumnsList:
            query_sql = query_sql + c + ', '
        query_sql = query_sql[0:-2] + " from %s"%("record_"+chat_id).strip()
    elif needColumnsList is None:
        query_sql = "select * from %s where fundCode in ("%("record_"+chat_id).strip()
        for fundCode in fundCodeList:
            query_sql = query_sql + fundCode + ","
        query_sql = query_sql[0:-1] + ")"
    else:
        query_sql = "select "
        for c in needColumnsList:
            query_sql = query_sql + c + ', '
        query_sql = query_sql[0:-2] + " from %s where fundCode in ("%("record_"+chat_id).strip()
        for fundCode in fundCodeList:
            query_sql = query_sql + "\'" +fundCode + "\',"
        query_sql = query_sql[0:-1] + ")"
    
    try:
        cur.execute(query_sql)
        result = cur.fetchall()
    except:
        result = "读取错误，请重试"
    finally:
        cur.close()
        conn.close()

    return result


def buyRecord(chat_id, updateList):
    

    reply_text = ""
    for record in updateList:
        # 字典格式: {"fundCode":{"cost_price": 123, "total":1234}}
        print(record)
        fundCode= list(record.keys())[0]
        cost_price, total_price = record[fundCode].items()
        cost_price = cost_price[1]
        total_price = total_price[1]
        update_sql = "UPDATE %s SET cost_price=%f, total=%f,isHold = 1 where fundCode = \'%s\'"%(("record_"+chat_id).strip(), cost_price, total_price, fundCode)
        conn = getConn(db='fund_helper')
        cur = conn.cursor()
        cur.execute(update_sql)
        try:
            cur.execute(update_sql)
            conn.commit()
            reply_text = reply_text + "%s记录完毕\n"%(fundCode)
        except:
            reply_text = reply_text + "\n\n错误，请重试"
        finally:
            cur.close()
            conn.close()
        
    return reply_text