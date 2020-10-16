# _*_ coding:utf-8 _*_
# @File  : routers.py
# @Time  : 2020-08-31 8:22
# @Author: zizle

from fastapi import APIRouter
from modules.basic import basic_router
from modules.user import user_router
from modules.industry import industry_router
from modules.update import updating_router
from modules.short_message import short_message_router
from modules.delivery import delivery_router
from modules.exchange_lib import exchange_router
from modules.report_file import report_file_router

router = APIRouter()

router.include_router(updating_router, tags=["版本更新"])
router.include_router(basic_router, tags=["客户端基本"])
router.include_router(user_router, tags=["用户"])
router.include_router(industry_router, tags=["行业数据"])
router.include_router(short_message_router, tags=["短信通"])
router.include_router(delivery_router, tags=["交割服务"])
router.include_router(exchange_router, tags=["交易所数据"])
router.include_router(report_file_router, tags=["报告处理"])
