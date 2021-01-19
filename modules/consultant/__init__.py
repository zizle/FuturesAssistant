# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2021-01-19 10:35
# @Author: zizle

from fastapi import APIRouter
from .article import article_api

consult_router = APIRouter()
consult_router.include_router(article_api, prefix='/article')
