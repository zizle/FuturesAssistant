# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2021-06-07 09:12
# @Author: zizle

# 用户接口(含后台管理员)

from fastapi import APIRouter
from .retrieve import retrieve_api

person_router = APIRouter()

person_router.include_router(retrieve_api)


