import efinance as ef
import os
import matplotlib.pyplot as plt

os.environ['NO_PROXY'] = 'push2his.eastmoney.com'

stock_code = '600577'
df = ef.stock.get_quote_history(stock_code, beg='20220501', end='20220816')


df['ma5'] = df['收盘'].rolling(5).mean()
df['ma10'] = df['收盘'].rolling(10).mean()
df['ma20'] = df['收盘'].rolling(20).mean()
df['ma30'] = df['收盘'].rolling(30).mean()

df[['ma5', 'ma10', 'ma20', 'ma30']].plot()
plt.show()
