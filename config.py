from configparser import ConfigParser

config = ConfigParser()

def getConfig(sectionName, configName):
    # 获取指定的配置信息
    config.read('config.json')
    config_value = config.get(sectionName, configName)
    return config_value

def getBotConfig():
    # 获取bot配置
    config.read('config.json')
    bot_token = config.get('bot_base', 'bot_token')
    bot_user_name = config.get('bot_base', 'bot_user_name')
    URL = config.get('bot_base', 'URL')

    return bot_token, bot_user_name, URL

def getSqlConfig():
    # 获取sql配置
    config.read('config.json')
    host = config.get('db', 'host')
    port = config.getint('db', 'port')
    user = config.get('db', 'user')
    password = config.get('db', 'password')
    
    return host, port, user, password

