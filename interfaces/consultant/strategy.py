# _*_ coding:utf-8 _*_
# @File  : strategy.py
# @Time  : 2021-01-19 15:13
# @Author: zizle

import datetime
from fastapi import APIRouter, Query, HTTPException, Body
from utils.verify import decipher_user_token
from db.mysql_z import MySqlZ

from .models import StrategyAddItem, StrategyModifyItem

strategy_api = APIRouter()


def handle_item(item):
    item['create_time'] = datetime.datetime.fromtimestamp(item['create_time']).strftime('%Y-%m-%d')
    return item


@strategy_api.get('/')  # 获取最近的100条交易策略
async def get_strategy(user_token: str = Query(...), admin: int = Query(0)):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录过期了,请重新登录!')
    is_admin = 1 if admin else 0
    if user_id <= 1:
        is_admin = 0
    # 查询数据
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT * FROM product_strategy WHERE IF(%s=0,TRUE,author_id=%s) "
            "ORDER BY create_time DESC LIMIT 100;",
            (is_admin, user_id)
        )
        strategy = cursor.fetchall()
    strategy = list(map(handle_item, strategy))
    return {'message': '查询成功!', 'strategy': strategy}


@strategy_api.post('/')  # 用户创建一条策略
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


@strategy_api.put('/{strategy_id}/')  # 用户修改一条策略
async def modify_strategy(strategy_item: StrategyModifyItem = Body(...)):
    user_id, _ = decipher_user_token(strategy_item.user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录过期了,请重新登录!')
    # 修改数据
    now_timestamp = int(datetime.datetime.now().timestamp())
    with MySqlZ() as cursor:
        cursor.execute(
            "UPDATE product_strategy SET update_time=%s,content=%s "
            "WHERE id=%s AND author_id=%s;",
            (now_timestamp, strategy_item.content, strategy_item.strategy_id, user_id)
        )
    return {'message': '修改成功!'}


@strategy_api.delete('/{strategy_id}/')  # 用户删除一条策略
async def delete_strategy(strategy_id: int, user_token: str = Query(...)):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录过期了,请重新登录!')
    with MySqlZ() as cursor:
        cursor.execute(
            "DELETE FROM product_strategy WHERE id=%s AND author_id=%s;",
            (strategy_id, user_id)
        )
    return {'message': '删除成功!如不是您创建的策略,刷新后仍会存在!'}

