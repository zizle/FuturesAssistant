# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2020-11-25 15:56
# @Author: zizle
""" 市场分析
主要为另一个客户端(价格-净持仓；价格指数)服务
"""
from fastapi import APIRouter
from .price_position import price_position_router
from .price_index import price_index_router

market_analysis_router = APIRouter()
market_analysis_router.include_router(price_position_router)
market_analysis_router.include_router(price_index_router)


