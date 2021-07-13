# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2020-08-03 8:19
# @Author: zizle
""" 系统更新模块 """

from fastapi import APIRouter
from .updating import updating_router

update_router = APIRouter()
update_router.include_router(updating_router)