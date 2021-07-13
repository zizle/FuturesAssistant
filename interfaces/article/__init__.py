# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2021-05-31 15:10
# @Author: zizle

from fastapi import APIRouter
from .analysis_article import analysis_article_api

article_router = APIRouter()

article_router.include_router(analysis_article_api)
