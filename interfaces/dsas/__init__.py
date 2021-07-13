# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2021-06-30  14:23
# @Author: zizle


# 数据分析整合接口

from fastapi import APIRouter
from .exchange import exchange_dsas_api

dsas_router = APIRouter()
dsas_router.include_router(exchange_dsas_api)
