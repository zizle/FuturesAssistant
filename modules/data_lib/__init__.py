# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2021-01-22 16:46
# @Author: zizle
from fastapi import APIRouter
from .exchange_rate import exchangelib_api

datalib_router = APIRouter()

datalib_router.include_router(exchangelib_api)
