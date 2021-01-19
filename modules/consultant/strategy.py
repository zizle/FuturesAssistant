# _*_ coding:utf-8 _*_
# @File  : strategy.py
# @Time  : 2021-01-19 15:13
# @Author: zizle

import datetime
from fastapi import APIRouter, Query, HTTPException, Body
from utils.verify import decipher_user_token
from db.mysql_z import MySqlZ

from .models import StrategyAddItem

strategy_api = APIRouter()


def handle_item(item):
    item['create_time'] = datetime.datetime.fromtimestamp(item['create_time']).strftime('%Y-%m-%d')
    return item

@strategy_api.get('/strategy/')  # 获取最近的100条交易策略
async def get_strategy(user_token: str = Query(...)):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录过期了,请重新登录!')
    # 查询数据
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT * FROM product_strategy WHERE IF(%s<1,TRUE,author_id=%s) "
            "ORDER BY create_time DESC LIMIT 100;",
            (user_id, user_id)
        )
        strategy = cursor.fetchall()
    strategy = list(map(handle_item, strategy))
    return {'message': '查询成功!', 'strategy': strategy}


@strategy_api.post('/strategy/')  # 用户创建一条策略
async def add_strategy(strategy_item: StrategyAddItem = Body(...)):
    user_id, _ = decipher_user_token(strategy_item.user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录过期了,请重新登录!')
    # 创建数据
    now_timestamp = int(datetime.datetime.now().timestamp())
    with MySqlZ() as cursor:
        cursor.execute(
            "INSERT INTO product_strategy (create_time,update_time,content,author_id) "
            "VALUES (%s,%s,%s,%s)",
            (now_timestamp, now_timestamp, strategy_item.content, user_id)
        )
    return {'message': '创建成功!'}



