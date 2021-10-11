import command
import re
from apscheduler.jobstores.base import JobLookupError

def schedule_query(chat_id):
    reply_text = command.queryAll(chat_id)
    return reply_text

def schedule(bot, chat_id):
    
    reply_text = schedule_query(chat_id)
    bot.sendMessage(chat_id=chat_id, text=reply_text)


def add_schedule(scheduler, bot, chat_id, add_schedule_text):
    reply_text = ""
    pattern = r'\d+'
    search = re.findall(pattern, add_schedule_text)
    for t in search:
      if int(t) < 0 or int(t) > 60:
        reply_text = "时间间隔只能在0-60之间"
      else:
        scheduler.add_job(
          schedule,
          trigger='cron',
          day_of_week='mon-fri',
          hour='9-11, 13-14',
          minute = '*/'+str(t),
          args=[bot, chat_id]
        )
        reply_text = "已完成"

    return reply_text

def delete_schedule(scheduler, delete_schedule_text):
    reply_text = ""
    search = delete_schedule_text.split(" ")
    finish = []
    for item in search:
        if item=="" or item == "remove" or item == "schedule" or item == "remove schedule":
            continue
        try:
            scheduler.remove_job(item)
            finish.append(item)
        except JobLookupError as e:
            reply_text = reply_text + "没有指定id的任务:{}\n".format(item)

    reply_text = reply_text + "已删除指定id任务: {}".format(" ".join(finish))
    return reply_text

def list_schedule(scheduler):
    scheduler_list = scheduler.get_jobs()
    if len(scheduler_list) == 0:
      reply_text = "没有任务"
    else:
      reply_text = ""
      for j in scheduler_list:
        tmp = "id: {}, 计划: {}, 下一次运行时间: {}".format(j.id, j.trigger, j.next_run_time)
        reply_text = reply_text + tmp + '\n\n'

    return reply_text