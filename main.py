# import everything
from flask import Flask, request
import telegram
from apscheduler.schedulers.background import BackgroundScheduler
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
      day_of_week='mon-fri',
      hour=14,
      minute=50,
      args=[bot, chat_id]
    )
    SCHEDULERED = True
    save.createTable(chat_id)

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
    if 'all' in text:
      reply_text = command.deleteAll(chat_id)
    else:
      if len(text.split(" ")) == 2:
        reply_text = "请输入需要删除的基金代码"
      else:
        delete_text = text.split(" ")[2:]
        reply_text = command.deleteRecord(chat_id, delete_text)
    bot.sendMessage(chat_id=chat_id, text=reply_text)
  
  elif "list my record" in text:
    reply_text = command.listRecord(chat_id)
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
      reply_text = schedule.delete_schedule(schedule, text)
      bot.sendMessage(chat_id=chat_id, text=reply_text)

  elif "list schedule" in text:
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