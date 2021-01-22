# _*_ coding:utf-8 _*_
# @File  : models.py
# @Time  : 2021-01-22 16:48
# @Author: zizle
from pydantic import BaseModel


class ExchangeRateAddItem(BaseModel):
    rate_date: str
    rate_name: str
    rate: float
