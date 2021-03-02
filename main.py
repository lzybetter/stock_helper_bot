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
  cursor.execute("create table if not exists \'{}\' (id INTEGER PRIMARY KEY AUTOINCREMENT, fundCode varchar(20))".format("record_" + str(chat_id)))
  cursor.close()
  conn.close()
  if not SCHEDULERED:
    scheduler.add_job(
      schedule_query,
      trigger='cron',
      day_of_week='mon-fri',
      hour=14,
      minute=30,
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
    - “delete all/clean” 清除所有的记录
    - “list record” 列出目前所有记录
    - “add schedule 分钟数” 增加一个定时器，在周一到周五的9点到15点之间按指定的间隔自动查询
    - “remove schedule id” 删除一个定时器
    - “list schedule” 列出所有的定时器
    - “help” 显示命令帮助
      PS：本bot会默认生成一个于周一到周五的每天14点30分运行的定时器，用于自动查询收盘前的涨跌幅
    """
    # send the welcoming message
    bot.sendMessage(chat_id=chat_id, text=bot_welcome)
  elif text == "help":
    help_text =  """
      “query 基金代号” 查询指定基金的单位净值及涨跌幅, 可同时查询多个基金
      “record 基金代号” 记录基金号, 可同时记录多个基金
      “delete 基金代号” 删除记录的基金代号，可同时删除多个基金
      “delete all/clean” 清除所有的记录
      “list record” 列出目前所有记录
      “add schedule 分钟数” 增加一个定时器，在周一到周五的9点到15点之间按指定的间隔自动查询
      “remove schedule id” 删除一个定时器
      “list schedule” 列出所有的定时器
      PS：本bot会默认生成一个于周一到周五的每天14点30分运行的定时器，用于自动查询收盘前的涨跌幅
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
      
      reply_text = queryFund(search, chat_id)

    bot.sendMessage(chat_id=chat_id, text=reply_text)
  
  elif "list record" in text:
    conn = sqlite3.connect('record.db')
    cursor = conn.cursor()
    cursor.execute("select fundCode from \'{}\'".format("record_" + str(chat_id)))
    lines = cursor.fetchall()
    reply_text = ""
    if len(lines) == 0:
      reply_text = "目前没有记录，请先建立记录"
    else:
      reply_text = "目前已有的记录：\n"
      for line in lines:
        reply_text = reply_text + line[0] + '\n'
      cursor.close()
      conn.close()
    bot.sendMessage(chat_id=chat_id, text=reply_text)

  elif "record" in text:
    conn = sqlite3.connect('record.db')
    cursor = conn.cursor()
    pattern = r'\d+'
    search = re.findall(pattern, text)
    cursor.execute("create table if not exists \'{}\' (id INTEGER PRIMARY KEY AUTOINCREMENT, fundCode varchar(20))".format("record_" + str(chat_id)))
    for i in search:
      if len(str(i)) != 6:
        bot.sendMessage(chat_id=chat_id, text="基金代码为6位，请检查")
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
          hour='9-15',
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
  with open('record.txt', 'r') as recordFile:
    lines = recordFile.readlines()

  if len(lines) < 1:
    return 0 
  
  lines = list(set(lines))
  reply_text = queryFund(lines)

  with open('record.txt', 'w') as recordFile:
    recordFile.writelines(lines)
  bot.sendMessage(chat_id=chat_id, text=reply_text)
  reply_text = ""

  return 1

def queryFund(items, chat_id=[]):
  reply_text = ""
  for item in items:

    if len(str(item.strip())) != 6:
      tmp ="基金代码为6位，请检查".format(str(item.strip()))
    else:
      try:
        res = requests.get("http://fundgz.1234567.com.cn/js/{}.js".format(item.strip()),timeout=30)
      except ReadTimeout as e:
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

if __name__ == '__main__':
  app.run()