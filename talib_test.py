import efinance as ef
import os
import matplotlib.pyplot as plt
import talib
import numpy as np

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111)

os.environ['NO_PROXY'] = 'push2his.eastmoney.com'

stock_code = '600577'
df = ef.stock.get_quote_history(stock_code, beg='20220401', end='20220926')


close = df['收盘'].values

df['macd'], df['macdsignal'], df['macdhist'] = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)

df = df.where(df['日期'] >= "2022-07-01")

red_bar = np.where(df['macd'] > 0, df['macd'], 0)
blue_bar = np.where(df['macd'] < 0, df['macd'], 0)

ax.bar(np.arange(0, len(df)), red_bar, color="red")
ax.bar(np.arange(0, len(df)), blue_bar, color="blue")

print(df.tail())

plt.show()


#
# df['K'], df['D'] = talib.STOCH(df['最高'].values,
#                                df['最低'].values,
#                                df['收盘'].values,
#                                fastk_period=9,
#                                slowk_period=3,
#                                slowk_matype=0,
#                                slowd_period=3,
#                               slowd_matype=0)
#
# ####处理数据，计算J值
# df['K'].fillna(0,inplace=True)
# df['D'].fillna(0,inplace=True)
# df['J']=3*df['K']-2*df['D']
#
# ####计算金叉和死叉
#
# df['KDJ_金叉死叉'] = ''
# ####令K>D 为真值
# kdj_position=df['K']>df['D']
#
# ####当Ki>Di 为真，Ki-1 <Di-1 为假 为金叉
# df.loc[kdj_position[(kdj_position == True) & (kdj_position.shift() == False)].index, 'KDJ_金叉死叉'] = '金叉'
#
# ####当Ki<Di 为真，Ki-1 >Di-1 为假 为死叉
# df.loc[kdj_position[(kdj_position == False) & (kdj_position.shift() == True)].index, 'KDJ_金叉死叉'] = '死叉'
#
# print(df)

