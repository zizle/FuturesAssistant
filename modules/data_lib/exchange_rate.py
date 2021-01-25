# _*_ coding:utf-8 _*_
# @File  : exchange_rate.py
# @Time  : 2021-01-22 16:47
# @Author: zizle

from fastapi import APIRouter, Body
from typing import List
from .models import ExchangeRateAddItem

datalib_api = APIRouter()


@datalib_api.post('/exchange-rate/')  # 上传汇率数据
async def exchange_rate(rate_items: List[ExchangeRateAddItem] = Body(...)):
    print(rate_items)
    return {'message': '上传成功!'}
