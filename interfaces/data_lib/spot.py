# _*_ coding:utf-8 _*_
# @File  : spot.py
# @Time  : 2021-07-14 15:26
# @Author: zizle
import datetime
import pandas as pd
from fastapi import APIRouter, Depends, Body
from pydantic import BaseModel
from typing import Optional, List
from db import FAConnection
from status import r_status
from interfaces.depends import logged_require,require_start_date, require_end_date
from configs import ADMIN_FLAG

spot_api = APIRouter()


class SpotItem(BaseModel):
    spot_date: str
    price: float
    src_note: str


@spot_api.post('/', summary='添加现货价格数据(一个或多个)')
async def create_spot_price(person: dict = Depends(logged_require), spot_data: Optional[List] = Body(...)):
    user_id = person['uid']
    # 处理数据入库
    df = pd.DataFrame(spot_data)
    df = df[df['price'] > 0]
    if df.empty:
        return {'code': r_status.NOT_CONTENT, 'message': f'保存现货价格数据成功无新增数据!'}
    df['spot_ts'] = df['spot_date'].apply(lambda x: int(datetime.datetime.strptime(x, '%Y-%m-%d').timestamp()))
    df['creator'] = [user_id for _ in range(df.shape[0])]
    del df['variety_name']
    del df['spot_date']
    save_data = df.to_dict(orient='records')
    save_sql = 'INSERT IGNORE INTO dat_spot_price (creator,spot_ts,variety_en,' \
               'price,src_note) ' \
               'VALUES (%(creator)s,%(spot_ts)s,%(variety_en)s,' \
               '%(price)s,%(src_note)s);'
    db = FAConnection(conn_name='Save Spots')
    count, _ = db.insert(save_sql, param=save_data, many=True, keep_conn=True)  # 先插入一波
    update_sql = 'UPDATE dat_spot_price SET creator=%(creator)s,price=%(price)s,src_note=%(src_note)s ' \
                 'WHERE spot_ts=%(spot_ts)s AND variety_en=%(variety_en)s;'
    update_count, _ = db.execute(update_sql, save_data, many=True)  # 再更新一波
    return {'code': r_status.CREATED_SUCCESS, 'message': f'保存现货价格数据成功,新增{count}个,更新{update_count}个.'}


@spot_api.get('/', summary='查询指定日期区间现货价格数据')
async def get_spot_price(ds: datetime.datetime = Depends(require_start_date),
                         de: datetime.datetime = Depends(require_end_date)):
    sql = 'SELECT id,spot_ts,variety_en,price,src_note FROM dat_spot_price WHERE spot_ts>=%s AND spot_ts<=%s;'
    db = FAConnection(conn_name='Query Date Spot')
    records = db.query(sql, [int(ds.timestamp()), int(de.timestamp())])
    for item in records:
        item['spot_date'] = datetime.datetime.fromtimestamp(int(item['spot_ts'])).strftime('%Y-%m-%d')
    return {'code': r_status.SUCCESS, 'message': '查询现货报价数据成功!', 'data': records}


@spot_api.get('.last/', summary='查询最新日期现货价格数据')
async def get_last_spot_price():
    sql = 'SELECT id,spot_ts,variety_en,price,src_note FROM dat_spot_price ' \
          'WHERE spot_ts=(SELECT MAX(spot_ts) FROM dat_spot_price);'
    db = FAConnection(conn_name='Query Date Spot')
    records = db.query(sql)
    df = pd.DataFrame(records)
    if df.empty:
        return {'code': r_status.SUCCESS, 'message': '查询最新现货报价数据成功!', 'data': []}
    df['spot_date'] = df['spot_ts'].apply(lambda x: datetime.datetime.fromtimestamp(x).strftime('%Y-%m-%d'))
    rep_data = df.to_dict(orient='records')
    return {'code': r_status.SUCCESS, 'message': '查询最新现货报价数据成功!', 'data': rep_data}


@spot_api.get('.userlast/', summary='查询用户权限品种的最新日期现货价格数据')
async def get_user_last_spot_price(person: dict = Depends(logged_require)):
    if ADMIN_FLAG in person['access']:
        sql = 'SELECT id,spot_ts,variety_en,price,src_note FROM dat_spot_price ' \
              'WHERE spot_ts=(SELECT MAX(spot_ts) FROM dat_spot_price);'
        param = None
    else:
        sql = 'SELECT s.id,s.spot_ts,s.variety_en,s.price,s.src_note ' \
              'FROM dat_spot_price AS s ' \
              'INNER JOIN ' \
              '(SELECT sv.variety_code,sp.user_id ' \
              'FROM sys_variety AS sv INNER JOIN sys_person_variety AS sp ON sv.id=sp.variety_id AND sp.user_id=%s) AS pv ' \
              'ON s.variety_en=pv.variety_code ' \
              'WHERE s.spot_ts=(SELECT MAX(spot_ts) FROM dat_spot_price WHERE variety_en=pv.variety_code);'
        param = [person['uid']]
    db = FAConnection(conn_name='查询用户最新现货')
    records = db.query(sql, param)
    df = pd.DataFrame(records)
    if df.empty:
        return {'code': r_status.SUCCESS, 'message': '查询用户最新的现货数据为空!', 'data': []}
    df['spot_date'] = df['spot_ts'].apply(lambda x: datetime.datetime.fromtimestamp(x).strftime('%Y-%m-%d'))

    rep_data = df.to_dict(orient='records')
    return {'code': r_status.SUCCESS, 'message': '查询用户最新的现货数据成功!', 'data': rep_data}

