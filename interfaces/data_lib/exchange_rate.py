# _*_ coding:utf-8 _*_
# @File  : exchange_rate.py
# @Time  : 2021-01-22 16:47
# @Author: zizle

import datetime
from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from typing import List
from db.mysql_z import MySqlZ
from .models import ExchangeRateAddItem

exchangelib_api = APIRouter()


def handle_save_date(item):  # 将保存的日期转为timestamp
    item['rate_timestamp'] = int(datetime.datetime.strptime(item['rate_date'], '%Y-%m-%d').timestamp())
    return item


@exchangelib_api.post('/exchange-rate/')  # 上传汇率数据
async def exchange_rate(rate_items: List[ExchangeRateAddItem] = Body(...)):
    rate_items = jsonable_encoder(rate_items)
    rate_items = list(map(handle_save_date, rate_items))
    # 保存入库
    if len(rate_items) < 1:
        raise HTTPException(status_code=400, detail='请上传汇率数据!')
    with MySqlZ() as cursor:
        count = cursor.executemany(
            "INSERT IGNORE INTO lib_exchange_rate (rate_timestamp,rate_name,rate) "
            "VALUES (%(rate_timestamp)s,%(rate_name)s,%(rate)s);",
            rate_items
        )
    return {'message': '上传成功!条目:{}'.format(count)}


@exchangelib_api.get('/exchange-rate/')  # 查询最新的汇率信息
async def get_exchange_lib():
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT rate_timestamp,rate_name,rate FROM lib_exchange_rate "
            "WHERE rate_timestamp=(SELECT MAX(rate_timestamp) FROM lib_exchange_rate);"
        )
        rate_data = cursor.fetchall()
    return {'message': '查询成功!', 'rates': rate_data}
