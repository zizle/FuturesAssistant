# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2020-08-31 8:45
# @Author: zizle
from fastapi import APIRouter
from .client import client_router
from .variety import variety_router
from .advertisement import ad_router

basic_router = APIRouter()

basic_router.include_router(client_router)
basic_router.include_router(variety_router)
basic_router.include_router(ad_router)

