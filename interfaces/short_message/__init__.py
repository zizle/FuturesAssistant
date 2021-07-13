# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2020-09-10 16:43
# @Author: zizle
""" 短讯通模块 """
from fastapi import APIRouter
from .short_msg import shortmsg_router

short_message_router = APIRouter()
short_message_router.include_router(shortmsg_router)