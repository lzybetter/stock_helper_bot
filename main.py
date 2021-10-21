# import everything
from flask import Flask, request
import telegram
import re
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
import config
import command
import save
import schedule

global bot
global TOKEN
global SCHEDULERED
SCHEDULERED = False
TOKEN, BOT_USER_NAME, URL = config.getBotConfig()
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
  chat_id = str(chat_id)
  msg_id = update.message.message_id
  save.createTable(chat_id)
  if not SCHEDULERED:
    scheduler.add_job(
      schedule.schedule,
      trigger='cron',
      day_of_week='mon-sun',
      hour=14,
      minute=50,
      args=[bot, chat_id]
    )
    SCHEDULERED = True

  # Telegram understands UTF-8, so encode text for unicode compatibility
  text = update.message.text.encode('utf-8').decode()
  
  if text == "/start":
    bot_welcome = """
    欢迎使用stock_helper_bot：
    请务必注意：由于接口限制，本bot的股票信息并非实时，存在15min以上的延迟！！！
    """
    # send the welcoming message
    bot.sendMessage(chat_id=chat_id, text=bot_welcome)
  elif text == "help":
    help_text =  """
    感谢使用stock_helper_bot，
    - “query 代码类型 代码” 查询指定股票/基金的最近价格及涨跌幅, 可同时查询多个股票/基金
    - “record 代码类型 代码” 记录股票/基金, 可同时记录多个股票/基金
    - “delete 代码” 删除记录的股票/基金，可同时删除多个股票/基金
    - “buy 代码类型 代码 购入成本 购入份数” 记录买入操作，可以同时添加多个买入记录
    - “sell 代码 卖出成本 卖出份数” 记录卖出操作，可以同时添加多个卖出记录
    - “sell 代码 all” 记录指定基金的清仓，可以同时进行多个基金的清仓
    - “list my hold” 列出目前所有的持仓记录
    - “delete all/clean” 清除所有的记录
    - “list record” 列出目前所有记录
    - “add schedule 分钟数” 增加一个定时器，在9点到16点之间按指定的间隔自动查询
    - “remove schedule id” 删除一个定时器
    - “list my schedule” 列出所有的定时器
    - “help” 显示命令帮助
    - 支持的股票/基金类型：A股(包括场内ETF):cn, 港股：hk，基金：fu，场外ETF：etf
    PS：
    - 本bot会默认生成一个每天14点50分运行的定时器，用于自动查询收盘前的涨跌幅；
    - 定时查询时，bot会自动检测开市情况，只在交易时段报告；
    - 由于接口限制，本bot的股票信息并非实时，存在15min以上的延迟！！！
    """
    bot.sendMessage(chat_id=chat_id, text=help_text)

  elif "query" in text:
    reply_text = ""
    if "all" in text:
      reply_text = command.queryAll(chat_id)
    else:
      if len(text.split(" ")) == 1:
        reply_text = "请输入需要查询的基金代码"
      else:
        query_text = text.split(" ")[1:]
        reply_text = command.queryCode(query_text)

    bot.sendMessage(chat_id=chat_id, text=reply_text)
  
  elif "add record" in text:
    reply_text = ""
    if len(text.split(" ")) == 2:
      reply_text = "请输入需要记录的基金代码"
    else:
      save_text = text.split(" ")[2:]
      reply_text = command.saveRecord(chat_id, save_text)
    
    bot.sendMessage(chat_id=chat_id, text=reply_text)

  elif "delete record" in text:
    reply_text = ""
    if len(text.split(" ")) == 2:
      reply_text = "请输入需要删除的基金代码"
    else:
      delete_text = text.split(" ")[2:]
      reply_text = command.deleteRecord(chat_id, delete_text)
    bot.sendMessage(chat_id=chat_id, text=reply_text)

  elif "list my record" in text:
    reply_text = command.listRecord(chat_id)    
    bot.sendMessage(chat_id=chat_id, text=reply_text)

  elif "change record name" in text:
    reply_text = ""
    if len(text.split(" ")) == 3:
      reply_text = "请输入需要改名的代码"
    else:
      change_text = text.split(" ")[3:]
      reply_text = command.changeName(chat_id, change_text)
    bot.sendMessage(chat_id=chat_id, text=reply_text)

  elif "buy" in text:
    # 输入为buy 类型 代码 单价 份数
    reply_text = ""
    lines = text.split(" ")[1:]
    if len(lines) < 4:
      reply_text = "您需要输入股票类型、股票代码、购入单价和购入份数"
    else:
      if len(lines)%4 != 0:
        reply_text = "每个股票都需要完整的输入股票类型、股票代码、购入单价和购入份数"
      else:
        reply_text = command.buyRecord(chat_id, lines)
    bot.sendMessage(chat_id=chat_id, text=reply_text)

  elif "sell" in text:
    # 输入为sell 代码 单价 份数
    reply_text = ""
    lines = text.split(" ")[1:]
    if len(lines) < 2:
      reply_text = "您需要输入股票代码、卖出单价和卖出份数"
    else:
        reply_text = command.sellRecord(chat_id, lines)

    bot.sendMessage(chat_id=chat_id, text=reply_text)
      
  elif "add schedule" in text:
    reply_text = schedule.add_schedule(scheduler, bot, chat_id, text)
    bot.sendMessage(chat_id=chat_id, text=reply_text)
  
  elif "remove schedule" in text:
    if "all" in text:
      scheduler.remove_all_jobs()
      reply_text = "已删除所有任务"
      bot.sendMessage(chat_id=chat_id, text=reply_text)

    else: 
      reply_text = schedule.delete_schedule(scheduler, text)
      bot.sendMessage(chat_id=chat_id, text=reply_text)

  elif "list my schedule" in text:
    reply_text = schedule.list_schedule(scheduler)
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

if __name__ == '__main__':
  app.run()