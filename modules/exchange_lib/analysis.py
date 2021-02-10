# _*_ coding:utf-8 _*_
# @File  : analysis.py
# @Time  : 2021-01-29 08:19
# @Author: zizle

"""
对交易所数据进行分析
"""

from fastapi import APIRouter

analysis_api = APIRouter()


@analysis_api.get('/correlation/')  # 对数据做相关性分析
async def correlation():
    return {}
