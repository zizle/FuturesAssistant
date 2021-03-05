# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2020-09-29 16:14
# @Author: zizle
""" 常规报告的API """

from fastapi import APIRouter
from .wechat_file import wechat_file_router
from .report import report_router

report_file_router = APIRouter()
report_file_router.include_router(wechat_file_router)
report_file_router.include_router(report_router)
