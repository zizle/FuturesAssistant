# _*_ coding:utf-8 _*_
# @File  : logger.py
# @Time  : 2021-03-08 09:03
# @Author: zizle

from loguru import logger

logger.add('debug/{time}.log', rotation='00:00', retention='20 days')
