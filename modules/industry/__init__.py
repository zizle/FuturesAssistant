# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2020-09-03 15:57
# @Author: zizle

""" 行业数据 """

from fastapi import APIRouter
from .user_sheet import sheet_router
from .user_chart import chart_router
from .spot_price import spot_price_router
from .user_folder import folder_router

industry_router = APIRouter()

industry_router.include_router(sheet_router)
industry_router.include_router(chart_router)
industry_router.include_router(spot_price_router)
industry_router.include_router(folder_router)

