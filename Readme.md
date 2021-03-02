## 一个用于查询基金的telegram机器人

### 部署：

请将telebot文件夹下的credentials.simple.py文件重命名为credentials.py，并在其中添加telegrambot的信息；

## 命令：

- “query 基金代号” 查询指定基金的单位净值及涨跌幅, 可同时查询多个基金

- “record 基金代号” 记录基金号, 可同时记录多个基金

- “delete 基金代号” 删除记录的基金代号，可同时删除多个基金

-  “delete all/clean” 清除所有的记录

-  “list record” 列出目前所有记录

- “add schedule 分钟数” 增加一个定时器，在`周一到周五`的9点到15点之间按指定的间隔自动查询

- “remove schedule id” 删除一个定时器

-  “list schedule” 列出所有的定时器

- “help” 显示命令帮助

   PS：本bot会默认生成一个于`周一到周五`的每天14点30分运行的定时器，用于自动查询收盘前的涨跌幅

