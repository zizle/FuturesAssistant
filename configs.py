# _*_ coding:utf-8 _*_
# @File  : configs.py
# @Time  : 2020-08-31 8:26
# @Author: zizle

""" 配置文件 """
import os
import time
import logging

APP_DIR = os.path.dirname(os.path.abspath(__file__))  # 项目根路径

FILE_STORAGE = "E:/FILE_STORAGE/"                                                       # 项目文件路径
WECHAT_FILE_PATH = "E:/WeChatFiles/WeChat Files/wxid_ebc8cjnovw1f22/FileStorage/File/"  # 微信自动保存的文件路径

SECRET_KEY = "cj3gnb1k2xzfq*odw5y-vts^+cv+p8suw+(_5#va%f70=tvt5mp"

JWT_EXPIRE_SECONDS = 6000


# 日志记录
def logger_handler(app_dir, log_level):
    # 日志配置
    log_folder = os.path.join(app_dir, "logs/")
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    log_file_name = time.strftime('%Y-%m-%d', time.localtime(time.time())) + '.log'
    log_file_path = log_folder + os.sep + log_file_name

    handler = logging.FileHandler(log_file_path, encoding='UTF-8')
    handler.setLevel(log_level)
    logger_format = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s - %(pathname)s[line:%(lineno)d]"
    )
    handler.setFormatter(logger_format)
    return handler


logger = logging.getLogger()
logger.addHandler(logger_handler(app_dir=APP_DIR, log_level=logging.INFO))

# 数据库配置
DB_CONFIGS = {
    # 系统主数据库
    "mysql": {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "mysql",
        "database": "futures_assistant"
    },
    # 用户品种数据表数据库(独立原因: 表数据和字段类型不确定)
    "variety_sheet": {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "mysql",
        "database": "fa_variety_sheets"
    },
    # 交易所数据数据库(独立原因: 较早开发,可不整合)
    "exchange_lib": {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "mysql",
        "database": "fa_exchange_lib"
    },
    "redis": {
        "host": "localhost",
        "port": "6379",
        "db": 1
    }
}
