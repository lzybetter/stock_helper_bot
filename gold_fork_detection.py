import efinance as ef
import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

os.environ['NO_PROXY'] = 'push2his.eastmoney.com'

today = datetime.today().date()
month_ago = today - timedelta(days=30)

today_str = datetime.strftime(today, "%Y%m%d")
month_ago_str = datetime.strftime(month_ago, "%Y%m%d")

print(today_str)
print(month_ago_str)

stock_code = '600577'
df = ef.stock.get_quote_history(stock_code, beg=month_ago_str, end=today_str)


df['ma5'] = df['收盘'].rolling(5).mean()
df['ma10'] = df['收盘'].rolling(10).mean()
df['ma20'] = df['收盘'].rolling(20).mean()
df['ma30'] = df['收盘'].rolling(30).mean()

df[['ma5', 'ma10', 'ma20', 'ma30']].plot()
plt.show()
