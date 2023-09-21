# 修改内容后，请将此文件改名为settings.py
# 爬虫代理，如果不使用代理，则不改动
PROXIES = {"http": "127.0.0.1:7890"}
# DB
MYSQL_SERVER_IP = '127.0.0.1'
MYSQL_SERVER_PORT = 3306
MYSQL_DB_NAME = "mysql"
MYSQL_USER_NAME = "root"
MYSQL_USER_PWD = "123456"

MONGO_SERVER_IP = '127.0.0.1'
MONGO_SERVER_PORT = 27017

CCF_FILE = "db_utils/ccf_2019.csv"
CCF_BAK_TABLE_NAME = "ccf_bak_2019"
CCF_TABLE_NAME = "ccf_2019"

# api
API_IP = "127.0.0.1"
API_PORT = "8002"

# 讯飞星火api
xunfei_config = "app_utils/config.json"
appid = "XXXX"     #填写控制台中获取的 APPID 信息
api_secret = "XXXXX"   #填写控制台中获取的 APISecret 信息
api_key ="XXXXX"    #填写控制台中获取的 APIKey 信息
#用于配置大模型版本，默认“general/generalv2”
# domain = "general"   # v1.5版本
domain = "generalv2"    # v2.0版本
#云端环境的服务地址
# Spark_url = "ws://spark-api.xf-yun.com/v1.1/chat"  # v1.5环境的地址
Spark_url = "ws://spark-api.xf-yun.com/v2.1/chat"  # v2.0环境的地址
