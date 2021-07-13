# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2020-08-31 8:23
# @Author: zizle


from fastapi import APIRouter

from .ruizy import ruizy_router
from .basic import basic_router
from .user import user_router
from .industry import industry_router
from .update import updating_router
from .short_message import short_message_router
from .delivery import delivery_router
from .exchange_lib import exchange_router
from .report_file import report_file_router
from .market_analysis import market_analysis_router
from .consultant import consult_router
from .data_lib import datalib_router
from .article import article_router
from .dsas import dsas_router


interface_api = APIRouter()

interface_api.include_router(ruizy_router, prefix='/ruizy', tags=['Ruizy'])

interface_api.include_router(updating_router, tags=["版本更新"])
interface_api.include_router(basic_router, tags=["客户端基本"])
interface_api.include_router(user_router, tags=["用户"])
interface_api.include_router(industry_router, tags=["行业数据"])
interface_api.include_router(short_message_router, tags=["短信通"])
interface_api.include_router(delivery_router, tags=["交割服务"])
interface_api.include_router(exchange_router, tags=["交易所数据"])
interface_api.include_router(report_file_router, tags=["报告处理"])
interface_api.include_router(market_analysis_router, tags=["市场分析-独立客户端服务"])
interface_api.include_router(consult_router, prefix='/consultant', tags=["产品服务-顾问服务"])
interface_api.include_router(datalib_router, prefix='/datalib', tags=["系统数据库"])
interface_api.include_router(article_router, prefix='/article', tags=['文章'])
interface_api.include_router(dsas_router, prefix='/dsas', tags=['数据分析'])


