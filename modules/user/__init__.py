# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2020-08-31 8:23
# @Author: zizle
from fastapi import APIRouter
from .passport import passport_router
from .views import user_view_router


user_router = APIRouter()
user_router.include_router(passport_router)
user_router.include_router(user_view_router)
