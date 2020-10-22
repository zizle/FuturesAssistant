# _*_ coding:utf-8 _*_
# @File  : encryptor.py
# @Time  : 2020-09-05 0:35
# @Author: zizle
import time
from datetime import datetime
from hashlib import md5
""" 生成，加密 """


def generate_chart_option_filepath(user_id: int):
    """ 生成图形配置的json文件相对路径 """
    hash_handler = md5(str(user_id).encode("utf-8"))
    hash_handler.update(str(time.time()).encode("utf-8"))
    today = datetime.today()
    filepath = "{}/{}/{}/{}.json".format(user_id, today.strftime("%Y"), today.strftime("%m"), hash_handler.hexdigest())
    return filepath


def generate_random_filename():
    hash_handler = md5(str(time.time()).encode("utf-8"))
    return hash_handler.hexdigest()

