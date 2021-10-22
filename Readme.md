## 一个用于查询股票/基金的telegram机器人

## 由于接口限制，本bot的股票信息并非实时，存在15min以上的延迟！！！

### 部署：

- 安装nginx，flask和uwsgi
- 安装mysql数据库，并设置用户名和密码

- 执行“pip3 install -r requirements”
- 将config.example.json复制为config.json，并在其中添加机器人和mysql数据库信息
- 执行：”uwsgi -s /tmp/uwsgi.sock -w main:app --logformat="%(method) %(uri) %(uagent)"  --uid www-data --gid www-data --enable-threads“

PS：请注意程序和文件夹都需要设置www-data的读写执行权限

## 命令：

- “query 代码类型 代码” 查询指定股票/基金的最近价格及涨跌幅, 可同时查询多个股票/基金

- “record 代码类型 代码” 记录股票/基金, 可同时记录多个股票/基金

- “delete 代码” 删除记录的股票/基金，可同时删除多个股票/基金

- “buy 代码类型 代码 购入成本 购入份数” 记录买入操作，可以同时添加多个买入记录

- “sell 代码 卖出成本 卖出份数” 记录卖出操作，可以同时添加多个卖出记录

- “sell 代码 all” 记录指定基金的清仓，可以同时进行多个基金的清仓

- “list my hold” 列出目前所有的持仓记录

- “delete all/clean” 清除所有的记录

- “list record” 列出目前所有记录

- “watch record” 关注股票/基金, 可同时关注多个股票/基金

- “unwatch record” 取消关注股票/基金, 可同时取消关注多个股票/基金

- “add schedule 分钟数” 增加一个定时器，在9点到16点之间按指定的间隔自动查询

- “remove schedule id” 删除一个定时器

- “list my schedule” 列出所有的定时器

- “help” 显示命令帮助

- 支持的股票/基金类型：A股(包括场内ETF):cn, 港股：hk，基金：fu，场外ETF：etf

  PS：

- 本bot会默认生成一个每天14点50分运行的定时器，用于自动查询收盘前的涨跌幅；

- 定时查询时，bot会自动检测开市情况，只在交易时段报告；

- 由于接口限制，本bot的股票信息并非实时，存在15min以上的延迟！！！

