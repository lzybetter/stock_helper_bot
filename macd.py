import efinance as ef
import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111)

os.environ['NO_PROXY'] = 'push2his.eastmoney.com'

stock_code = '600577'
df = ef.stock.get_quote_history(stock_code, beg='20220601', end='20220926')

df['日期'] = pd.to_datetime(df['日期'])
df['日期'] = df['日期'].apply(lambda x: x.strftime('%Y-%m-%d'))
EMA1=df["收盘"].ewm(span=12, adjust=False).mean()
EMA2=df["收盘"].ewm(span=26, adjust=False).mean()
df['DIF'] = EMA1 - EMA2
df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
df['BAR'] = 2 * (df['DIF'] - df['DEA'])

red_bar = np.where(df['BAR'] > 0, df['BAR'], 0)
blue_bar = np.where(df['BAR'] < 0, df['BAR'], 0)

ax.plot(np.arange(0, len(df)), df['DIF'])
ax.plot(np.arange(0, len(df)), df['DEA'])

ax.bar(np.arange(0, len(df)), red_bar, color="red")
ax.bar(np.arange(0, len(df)), blue_bar, color="blue")


gold_fork = df[(df['DIF'] > df['DEA']) & ((df['DIF'] <= df['DEA']).shift(1))]
dead_fork = df[(df['DIF'] <= df['DEA']) & ((df['DIF'] > df['DEA']).shift(1))]
parietal_deviation = df[(df['BAR'] > df['BAR'].shift(1)) & (df['BAR'].shift(-1) < df['BAR']) & (df['BAR'] > 0)]
bottom_deviation = df[(df['BAR'] < df['BAR'].shift(1)) & (df['BAR'].shift(-1) > df['BAR']) & (df['BAR'] < 0)]

print("金叉日期：" + gold_fork['日期'].values)
print("死叉日期：" + dead_fork['日期'].values)
print("顶背离日期：" + parietal_deviation['日期'].values)
print("底背离日期：" + bottom_deviation['日期'].values)


plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
plt.title("MACD")
plt.show()


