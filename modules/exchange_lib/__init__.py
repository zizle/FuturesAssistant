# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2020-07-23 21:40
# @Author: zizle

""" 交易所数据模块 """

from fastapi import APIRouter
from .saver import saver_router
from .queryer import query_router
from .position import position_router

exchange_router = APIRouter()

exchange_router.include_router(saver_router)
exchange_router.include_router(query_router)
exchange_router.include_router(position_router)

