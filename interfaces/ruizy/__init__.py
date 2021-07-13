# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2021-07-13 11:30
# @Author: zizle


from fastapi import APIRouter
from .ruizy import ruizy_api

ruizy_router = APIRouter()
ruizy_router.include_router(ruizy_api)

