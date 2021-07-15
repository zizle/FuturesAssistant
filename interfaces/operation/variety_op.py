# _*_ coding:utf-8 _*_
# @File  : variety_op.py
# @Time  : 2021-06-22  14:13
# @Author: zizle


# 系统品种接口

from fastapi import APIRouter, Depends, Body, Path
from pydantic import BaseModel
from db import FAConnection
from interfaces.depends import admin_logged_require
from status import r_status

op_variety_api = APIRouter()


class VarietyItem(BaseModel):
    category: int
    exchange: int
    variety_code: str
    variety_name: str
    is_active: int


@op_variety_api.post('/variety/', summary='新建一个品种')
async def create_variety(person: dict = Depends(admin_logged_require), variety_item: VarietyItem = Body(...)):
    creator = person['uid']
    variety_code = variety_item.variety_code.upper()
    print(variety_code)
    db = RuiZyDBConnection(conn_name='create-variety')
    # 查询是否已经存在
    query_sql = 'SELECT id FROM sys_variety WHERE variety_code=%s AND exchange=%s;'
    record = db.query(query_sql, [variety_code, variety_item.exchange], keep_conn=True)
    if len(record) > 0:
        db.close()
        return {'code': r_status.VALIDATE_ERROR, 'message': '品种已存在!无需重复添加'}
    sql = 'INSERT INTO sys_variety (creator,category,exchange,variety_code,variety_name) ' \
          'VALUES (%s,%s,%s,%s,%s);'

    count, _ = db.insert(sql, [creator, variety_item.category, variety_item.exchange, variety_code,
                               variety_item.variety_name])
    if count:
        return {'code': r_status.CREATED_SUCCESS, 'message': '创建成功!'}
    else:
        return {'code': r_status.UNKNOWN_ERROR, 'message': '创建失败,原因未知!'}


@op_variety_api.put('/variety/{variety_id}/', summary='修改一个品种')
async def update_variety(person: dict = Depends(admin_logged_require), variety_id: int = Path(..., ge=1),
                         variety_item: VarietyItem = Body(...)):
    creator = person['uid']
    sql = 'UPDATE sys_variety SET creator=%s,category=%s,exchange=%s,variety_code=%s,variety_name=%s,is_active=%s ' \
          'WHERE id=%s;'
    variety_code = variety_item.variety_code.upper()
    db = RuiZyDBConnection(conn_name='update-variety')
    count, _ = db.insert(sql, [creator, variety_item.category, variety_item.exchange, variety_code,
                               variety_item.variety_name, variety_item.is_active, variety_id])
    if count:
        return {'code': r_status.SUCCESS, 'message': '修改成功!'}
    else:
        return {'code': r_status.UNKNOWN_ERROR, 'message': '修改失败,请确认是否同交易所同品种问题!'}



