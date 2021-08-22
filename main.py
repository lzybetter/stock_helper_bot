# import everything
from flask import Flask, request
import telegram
from telebot.credentials import bot_token, bot_user_name, URL
import requests
from requests.exceptions import ReadTimeout
import json
import re
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
import sqlite3

global bot
global TOKEN
global SCHEDULERED
SCHEDULERED = False
TOKEN = bot_token
bot = telegram.Bot(token=TOKEN)
bot.setWebhook(URL+'/{}'.format(TOKEN))

# start the flask app
app = Flask(__name__)

scheduler = BackgroundScheduler()
scheduler.start()


@app.route('/{}'.format(TOKEN), methods=['POST','GET'])
def respond():
  global SCHEDULERED
  # retrieve the message in JSON and then transform it to Telegram object
  update = telegram.Update.de_json(request.get_json(force=True), bot)
  if update is None or update.message is None or update.message.text is None:
    return 'Error'
  chat_id = update.message.chat.id
  msg_id = update.message.message_id
  conn = sqlite3.connect('record.db')
  cursor = conn.cursor()
  cursor.execute("create table if not exists \'{}\' (id INTEGER PRIMARY KEY AUTOINCREMENT, fundCode VARCHAR(20), amount DEFAULT 0, bill DEFAULT 0, nav DEFAULT 0, isHold DEFAULT 0)".format("record_" + str(chat_id)))
  cursor.close()
  conn.close()
  if not SCHEDULERED:
    scheduler.add_job(
      schedule_query,
      trigger='cron',
      day_of_week='mon-fri',
      hour=14,
      minute=50,
      args=[bot, chat_id]
    )
    SCHEDULERED = True

  # Telegram understands UTF-8, so encode text for unicode compatibility
  text = update.message.text.encode('utf-8').decode()
  
  if text == "/start":
    bot_welcome = """
    欢迎使用FundBot，
    - “query 基金代号” 查询指定基金的单位净值及涨跌幅, 可同时查询多个基金
    - “record 基金代号” 记录基金号, 可同时记录多个基金
    - “delete 基金代号” 删除记录的基金代号，可同时删除多个基金
    - “buy 基金代号 购入金额 购入份数” 记录买入操作，可以同时添加多个买入记录
    - “sell 基金代号 卖出金额 卖出份数” 记录卖出操作，可以同时添加多个卖出记录
    - “sell 基金代号 all” 记录指定基金的清仓，可以同时进行多个基金的清仓
    - “sell all” 同时记录全部基金的清仓
    - “list my hold” 列出目前所有的持仓记录
    - “delete all/clean” 清除所有的记录
    - “list record” 列出目前所有记录
    - “add schedule 分钟数” 增加一个定时器，在周一到周五的9点到15点之间按指定的间隔自动查询
    - “remove schedule id” 删除一个定时器
    - “list schedule” 列出所有的定时器
    - “help” 显示命令帮助
      PS：本bot会默认生成一个于周一到周五的每天14点50分运行的定时器，用于自动查询收盘前的涨跌幅
    """
    # send the welcoming message
    bot.sendMessage(chat_id=chat_id, text=bot_welcome)
  elif text == "help":
    help_text =  """
    感谢使用FundBot，
    - “query 基金代号” 查询指定基金的单位净值及涨跌幅, 可同时查询多个基金
    - “record 基金代号” 记录基金号, 可同时记录多个基金
    - “delete 基金代号” 删除记录的基金代号，可同时删除多个基金
    - “buy 基金代号 购入金额 购入份数” 记录买入操作，可以同时添加多个买入记录
    - “sell 基金代号 卖出金额 卖出份数” 记录卖出操作，可以同时添加多个卖出记录
    - “sell 基金代号 all” 记录指定基金的清仓，可以同时进行多个基金的清仓
    - “sell all” 同时记录全部基金的清仓
    - “list my hold” 列出目前所有的持仓记录
    - “delete all/clean” 清除所有的记录
    - “list record” 列出目前所有记录
    - “add schedule 分钟数” 增加一个定时器，在周一到周五的9点到15点之间按指定的间隔自动查询
    - “remove schedule id” 删除一个定时器
    - “list schedule” 列出所有的定时器
    - “help” 显示命令帮助
      PS：本bot会默认生成一个于周一到周五的每天14点50分运行的定时器，用于自动查询收盘前的涨跌幅
    """
    bot.sendMessage(chat_id=chat_id, text=help_text)

  elif "query" in text:
    if "all" in text:
      conn = sqlite3.connect('record.db')
      cursor = conn.cursor()
      cursor.execute("select fundCode from \'{}\'".format("record_" + str(chat_id)))
      lines = cursor.fetchall()
      reply_text = ""
      if len(lines) == 0:
        reply_text = "目前没有记录，请先建立记录"
      else:
        tmp = []
        for line in lines:
          tmp.append(line[0])
        lines = list(set(tmp))
        reply_text = queryFund(lines)
      cursor.close()
      conn.close()
    else:
      pattern = r'\d+'
      search = re.findall(pattern, text)
      if len(search) == 0:
        reply_text = "请输入需要查询的基金代码"
      else:
        reply_text = queryFund(search, chat_id)

    bot.sendMessage(chat_id=chat_id, text=reply_text)
  
  elif "list record" in text:
    conn = sqlite3.connect('record.db')
    cursor = conn.cursor()
    cursor.execute("select fundCode, isHold from \'{}\'".format("record_" + str(chat_id)))
    lines = cursor.fetchall()
    reply_text = ""
    if len(lines) == 0:
      reply_text = "目前没有记录，请先建立记录"
    else:
      reply_text = "目前已有的记录：\n"
      for line in lines:
        if line[1] == 0:
          reply_text = reply_text + line[0] + " 未持有" + '\n'
        else:
          reply_text = reply_text + line[0] + " 持有" + '\n'
          
    cursor.close()
    conn.close()
    bot.sendMessage(chat_id=chat_id, text=reply_text)

  elif "list my hold" in text:
    conn = sqlite3.connect('record.db')
    cursor = conn.cursor()
    cursor.execute("select fundCode, amount, bill, nav from \'{}\' where isHold=1".format("record_" + str(chat_id)))
    lines = cursor.fetchall()
    reply_text = ""
    if len(lines) == 0:
      reply_text = "目前没有记录持仓信息，请先记录"
    else:
      reply_text = "目前持仓记录：\n"
      for line in lines:
        tmp = "基金代码: {}, 持仓金额: {}, 持仓份数: {}, 平均净值: {}".format(line[0], str(line[1]), str(line[2]), str(line[3]))
        reply_text = reply_text + tmp + '\n'
    cursor.close()
    conn.close()
    bot.sendMessage(chat_id=chat_id, text=reply_text)

  elif "record" in text:
    conn = sqlite3.connect('record.db')
    cursor = conn.cursor()
    pattern = r'\d+'
    search = re.findall(pattern, text)
    cursor.execute("create table if not exists \'{}\' (id INTEGER PRIMARY KEY AUTOINCREMENT, fundCode VARCHAR(20), amount DEFAULT 0, bill DEFAULT 0, nav DEFAULT 0, isHold DEFAULT 0)".format("record_" + str(chat_id)))
    for i in search:
      if len(str(i)) != 6:
        bot.sendMessage(chat_id=chat_id, text="基金代码为6位，请检查")
        continue
      cursor.execute("select id from \'{}\' where fundCode = \'{}\'".format("record_" + str(chat_id), str(i)))
      r = cursor.fetchall()
      if len(r) != 0:
        bot.sendMessage(chat_id=chat_id, text="{}已有记录，不再重新记录".format(str(i)))
        continue
      cursor.execute("insert into \'{}\' (fundCode) values (\'{}\')".format("record_" + str(chat_id), str(i)))
    cursor.close()
    conn.commit()
    conn.close()
    reply_text = "record finish"    
    bot.sendMessage(chat_id=chat_id, text=reply_text)

  elif "delete" in text:
    reply_text = "删除失败"
    conn = sqlite3.connect('record.db')
    cursor = conn.cursor()
    cursor.execute("select fundCode from \'{}\'".format("record_" + str(chat_id)))
    lines = cursor.fetchall()

    if len(lines) == 0:
      reply_text = "没有记录"
    elif "all" in text:
      cursor.execute("delete from \'{}\'".format("record_" + str(chat_id)))
      cursor.execute("update sqlite_sequence set seq = 0 where name = \'{}\'".format("record_" + str(chat_id)))
      cursor.execute("delete from sqlite_sequence where name = \'{}\'".format("record_" + str(chat_id)))
      cursor.execute("delete from sqlite_sequence")
      reply_text = "已清除全部记录"
    else:
      pattern = r'\d+'
      search = re.findall(pattern, text)

      tmp = []
      for line in lines:
        tmp.append(line[0])
      lines = list(set(tmp))
      if len(lines) == 0:
        reply_text = "没有记录"
      else: 
        for item in search:
          if item in lines:
            cursor.execute("delete from \'{}\' where fundCode = \'{}\'".format("record_" + str(chat_id), str(item)))
          else:
            bot.sendMessage(chat_id=chat_id, text="没有记录:{}".format(str(item)))
        reply_text = "删除完毕"
    cursor.close()
    conn.commit()
    conn.close()
    bot.sendMessage(chat_id=chat_id, text=reply_text)

  elif "buy" in text:

    search = text.split(" ")
    if len(search) < 4:
      bot.sendMessage(chat_id=chat_id, text="您需要输入基金代码、购入金额和持有份数")
      return 'Error 3'
    search = search[1:]
    if len(search)%3 != 0:
      bot.sendMessage(chat_id=chat_id, text="每个基金都需要完整的输入基金代码、购入金额和持有份数")
      return 'Error 4'
    conn = sqlite3.connect('record.db')
    cursor = conn.cursor()
    cursor.execute("create table if not exists \'{}\' (id INTEGER PRIMARY KEY AUTOINCREMENT, fundCode VARCHAR(20), amount REAL DEFAULT 0, bill REAL DEFAULT 0, nav REAL DEFAULT 0, isHold INTEGER DEFAULT 0)".format("record_" + str(chat_id)))
    num = int(len(search)/3)
    for i in range(num):
      fundCode = search[i*3]
      if isNumber(search[i*3 + 1]) and isNumber(search[i*3 + 2]):
        amount = float(search[i*3 + 1])
        bill = float(search[i*3 + 2])
        if amount <= 0 or bill <= 0:
          bot.sendMessage(chat_id=chat_id, text="购入金额和持有份数只能为正值: {},{},{}".format(fundCode, str(amount), str(bill)))
          continue
      else:
        bot.sendMessage(chat_id=chat_id, text="购入金额和持有份数只能为整数或小数: {},{},{}".format(fundCode, str(amount), str(bill)))
        continue
      if len(fundCode) != 6:
        bot.sendMessage(chat_id=chat_id, text="基金代码为6位，请检查".format(fundCode))
        continue
      else:
        cursor.execute("select fundCode, amount, bill from \'{}\' where fundCode = \'{}\'".format("record_" + str(chat_id), str(fundCode)))
        r = cursor.fetchall()
        if len(r) == 0:
          nav = round(amount/bill, 4)
          cursor.execute("insert into \'{}\' (fundCode, amount, bill, nav, isHold) values (\'{}\', {}, {}, {}, {})".format("record_" + str(chat_id), str(fundCode), amount, bill, nav, 1))
        else:
          result = r[0]
          amount = result[1] + amount
          bill = result[2] + bill
          nav = round(amount/bill, 4)
          cursor.execute("update \'{}\' set amount={}, bill={}, nav={}, isHold={} where fundCode=\'{}\'".format("record_" + str(chat_id), amount, bill, nav, 1, str(fundCode)))
        reply_text = "基金代码: {}, 持有金额: {}, 持有份数: {}, 平均净值: {}".format(str(fundCode), str(amount), str(bill), str(nav))
        bot.sendMessage(chat_id=chat_id, text=reply_text)
    cursor.close()
    conn.commit()
    conn.close()
    bot.sendMessage(chat_id=chat_id, text="已完成记录")
  elif "sell" in text:

    conn = sqlite3.connect('record.db')
    cursor = conn.cursor()
    
    if text == "sell all":
      # 卖出全部
      cursor.execute("select fundCode from \'{}\'".format("record_" + str(chat_id)))
      lines = cursor.fetchall()

      if len(lines) == 0:
        bot.sendMessage(chat_id=chat_id, text="没有记录请先建立记录")
        return 'Error 1'

      cursor.execute("select fundCode, amount, bill, nav from \'{}\' where isHold = 1".format("record_" + str(chat_id)))
      lines = cursor.fetchall()
      if len(lines) == 0:
        bot.sendMessage(chat_id=chat_id, text="目前没有记录持仓信息")
      else:
        reply_text = "已清仓:\n"
        for line in lines:
          tmp = "基金代码: {}, 总金额: {}, 总份额: {}, 平均净值: {}".format(line[0], line[1], line[2], line[3])
          reply_text = reply_text + tmp + '\n'
        cursor.execute("update \'{}\' set amount={}, bill={}, nav={}, isHold={}".format("record_" + str(chat_id), 0, 0, 0, 0))
        bot.sendMessage(chat_id=chat_id, text=reply_text)
    else: 
      search = text.split(" ")[1:]
      # if len(search) < 2:
      #   bot.sendMessage(chat_id=chat_id, text="您需要输入基金代码、卖出金额和卖出份数\n或输入sell all来表示清空全部持仓记录")
      #   return 'Error 3'
      num = 0
      fundCodeError = False
      amountError = False
      for s in search:
        if num == 0:
          num = num + 1
          fundCode = s
          if len(s) != 6:
            bot.sendMessage(chat_id=chat_id, text="基金代码为6位，请检查".format(s))
            fundCodeError = True
        elif num == 1:
          num = num + 1
          if s == "all":
            num = 0
            if fundCodeError:
              fundCodeError = False
              continue
            # 将单个基金清空的逻辑
            cursor.execute("select amount, bill, nav, isHold from \'{}\' where fundCode = \'{}\'".format("record_" + str(chat_id), fundCode))
            lines = cursor.fetchall()
            if len(lines) == 0:
              bot.sendMessage(chat_id=chat_id, text="目前没有记录持仓信息")
            elif lines[0][3] == 0:
              bot.sendMessage(chat_id=chat_id, text="目前没有该基金的持仓记录: {}".format(fundCode))
            else:
              cursor.execute("update \'{}\' set amount={}, bill={}, nav={}, isHold={} where fundCode=\'{}\'".format("record_" + str(chat_id), 0, 0, 0, 0, str(fundCode)))
              reply_text = "已清仓:\n 基金代码: {}, 总金额: {}, 总份额: {}, 平均净值: {}".format(fundCode, lines[0][0], lines[0][1], lines[0][2])
              bot.sendMessage(chat_id=chat_id, text=reply_text)
          else:
            amount = s
            if isNumber(s):
              amount = float(s)
              if amount <= 0: 
                bot.sendMessage(chat_id=chat_id, text="卖出金额只能为正值: {},{}".format(fundCode, str(amount)))
                amountError = True
            else:
              bot.sendMessage(chat_id=chat_id, text="卖出金额只能为数值: {},{}".format(fundCode, str(amount)))
              amountError = True
        elif num == 2:
          num = 0
          if amountError or fundCodeError:
            fundCodeError = False
            amountError = False
            continue
          bill = s
          if isNumber(s):
            bill = float(s)
            if bill <= 0: 
              bot.sendMessage(chat_id=chat_id, text="卖出金额只能为正值: {},{}".format(fundCode, str(bill)))
            else:
              cursor.execute("select amount, bill, nav, isHold from \'{}\' where fundCode = \'{}\'".format("record_" + str(chat_id), fundCode))
              lines = cursor.fetchall()
              if len(lines) == 0:
                bot.sendMessage(chat_id=chat_id, text="目前没有记录持仓信息: {}".format(fundCode))
              elif lines[0][3] == 0:
                bot.sendMessage(chat_id=chat_id, text="目前没有该基金的持仓记录: {}".format(fundCode))
              else:
                hisAmount = lines[0][0]
                hisBill = lines[0][1]
                if amount > hisAmount or bill > hisBill:
                  bot.sendMessage(chat_id=chat_id, text="卖出金额/份数不能大于持有的金额/份数: {}, {}, {}".format(fundCode, str(amount), str(bill)))
                elif amount == hisAmount and bill != hisBill:
                  bot.sendMessage(chat_id=chat_id, text="持仓金额已为0，持仓份数却不等于0，请检查: {}, {}, {}".format(fundCode, str(amount), str(bill)))
                elif amount != hisAmount and bill == hisBill:
                  bot.sendMessage(chat_id=chat_id, text="持仓份数已为0，持仓金额却不等于0，请检查: {}, {}, {}".format(fundCode, str(amount), str(bill)))
                else:
                  newAmount = hisAmount - amount
                  newBill = hisBill - bill
                  newNav = round(newAmount/newBill, 4)
                  cursor.execute("update \'{}\' set amount={}, bill={}, nav={}, isHold={} where fundCode=\'{}\'".format("record_" + str(chat_id), newAmount, newBill, newNav, 1, str(fundCode)))
                  reply_text = "已卖出:\n基金代码: {}, 卖出金额: {}, 卖出份数: {}, 卖出净值: {}\n目前持有:\n基金代码: {}, 持有金额: {}, 持有份数: {}, 持有净值: {}".format(fundCode, str(amount), str(bill), str(round(amount/bill, 4)), fundCode, str(newAmount), str(newBill), str(newNav))
                  bot.sendMessage(chat_id=chat_id, text=reply_text)
          else:
            bot.sendMessage(chat_id=chat_id, text="卖出金额只能为数值: {},{}".format(fundCode, str(bill)))
          fundCode = ""
          amount = 0
          bill = 0

    cursor.close()
    conn.commit()
    conn.close()
    bot.sendMessage(chat_id=chat_id, text="已完成记录")      

  elif text == "clean":
    conn = sqlite3.connect('record.db')
    cursor = conn.cursor()
    cursor.execute("delete from \'{}\'".format("record_" + str(chat_id)))
    cursor.execute("update sqlite_sequence set seq = 0 where name = \'{}\'".format("record_" + str(chat_id)))
    cursor.execute("delete from sqlite_sequence where name = \'{}\'".format("record_" + str(chat_id)))
    cursor.execute("delete from sqlite_sequence")
    cursor.close()
    conn.commit()
    conn.close()
    reply_text = "已清除全部记录"
    bot.sendMessage(chat_id=chat_id, text=reply_text)
  
  elif "add schedule" in text:
    pattern = r'\d+'
    search = re.findall(pattern, text)
    for t in search:
      if int(t) < 0 or int(t) > 60:
        bot.sendMessage(chat_id=chat_id, text="时间间隔只能在0-60之间")
      else:
        scheduler.add_job(
          schedule_query,
          trigger='cron',
          day_of_week='mon-fri',
          hour='9-11, 13-14',
          minute = '*/'+str(t),
          args=[bot, chat_id]
        )
        reply_text = "已完成"
        bot.sendMessage(chat_id=chat_id, text=reply_text)
  
  elif "remove schedule" in text:
    if "all" in text:
      scheduler.remove_all_jobs()
      reply_text = "已删除所有任务"
      bot.sendMessage(chat_id=chat_id, text=reply_text)
    else: 
      search = text.split(" ")
      finish = []
      for item in search:
        if item=="" or item == "remove" or item == "schedule" or item == "remove schedule":
          continue
        try:
          scheduler.remove_job(item)
          finish.append(item)
        except JobLookupError as e:
          bot.sendMessage(chat_id=chat_id, text="没有指定id的任务:{}".format(item))

      reply_text = "已删除指定id任务: {}".format(" ".join(finish))
      bot.sendMessage(chat_id=chat_id, text=reply_text)

  elif "list schedule" in text:
    scheduler_list = scheduler.get_jobs()
    if len(scheduler_list) == 0:
      reply_text = "没有任务"
    else:
      reply_text = ""
      for j in scheduler_list:
        tmp = "id: {}, 计划: {}, 下一次运行时间: {}".format(j.id, j.trigger, j.next_run_time)
        reply_text = reply_text + tmp + '\n\n'
    bot.sendMessage(chat_id,text=reply_text)

  else:
    reply_text = "Unkown Command"
    bot.sendMessage(chat_id=chat_id, text=reply_text, reply_to_message_id=msg_id)

  return 'ok'

@app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    # we use the bot object to link the bot to our app which live
    # in the link provided by URL
    s = bot.setWebhook(URL+'/{}'.format(TOKEN))
    # something to let us know things work
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"

@app.route('/')
def index():
   return '.'

def schedule_query(bot, chat_id):

  conn = sqlite3.connect('record.db')
  cursor = conn.cursor()
  cursor.execute("select fundCode from \'{}\'".format("record_" + str(chat_id)))
  lines = cursor.fetchall()
  reply_text = ""
  if len(lines) == 0:
    reply_text = "目前没有记录，请先建立记录"
  else:
    tmp = []
    for line in lines:
      tmp.append(line[0])
    lines = list(set(tmp))
    reply_text = queryFund(lines)
    
  bot.sendMessage(chat_id=chat_id, text=reply_text)
  cursor.close()
  conn.close()

  return 1

def queryFund(items, chat_id=[]):
  reply_text = ""
  for item in items:

    if len(str(item.strip())) != 6:
      tmp ="基金代码为6位，请检查".format(str(item.strip()))
    else:
      try:
        res = requests.get("http://fundgz.1234567.com.cn/js/{}.js".format(item.strip()),timeout=5)
      except ReadTimeout as e:
        tmp = "基金代码: {}, 查询超时，请稍后再试".format(str(item.strip()))
        continue
      # 正则表达式
      pattern = r'^jsonpgz\((.*)\)'
      # 查找结果
      fundsearch = re.findall(pattern, res.text)
      if len(fundsearch) == 0 or len(fundsearch[0]) == 0:
        tmp = "不存在该基金代码：{}".format(item.strip())
      # 遍历结果
      else:
        for fundItem in fundsearch:
          data = json.loads(fundItem)
        # print(data,type(data))
          tmp = "基金代码: {}, 基金: {}, 当前净值: {},涨跌: {}%,更新时间: {}".format(data['fundcode'], data['name'], data['gsz'],data['gszzl'], data['gztime'])
    reply_text = reply_text + "\n\n" + tmp

  return reply_text

def isNumber(num):
  pattern = r'^[-+]?[-0-9]\d*\.\d*|[-+]?\.?[0-9]\d*$'
  result = re.match(pattern, num)
  return result

if __name__ == '__main__':
  app.run()