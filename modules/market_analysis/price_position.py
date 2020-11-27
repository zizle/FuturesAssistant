# _*_ coding:utf-8 _*_
# @File  : price_position.py
# @Time  : 2020-11-26 09:15
# @Author: zizle
import datetime
import math
import pandas as pd
from fastapi import APIRouter, Query
from db.mysql_z import MySqlZ

"""
API-1: 获取价格持仓指定品种下的所有合约
API-2: 获取合约的时间跨度
API-3: 价格-持仓数据
"""


price_position_router = APIRouter()


@price_position_router.get('/price-position-contracts/', summary='获取品种价格持仓的所有合约')
async def price_position_contract(variety_en: str = Query(..., min_length=1, max_length=2)):
    with MySqlZ() as m_cursor:
        m_cursor.execute(
            "SELECT id,contract "
            "FROM contribute_price_position "
            "WHERE variety_en=%s "
            "GROUP BY contract "
            "ORDER BY contract DESC;",
            variety_en
        )
        all_contract = m_cursor.fetchall()
    return {'message': '查询成功!', 'contracts': all_contract}


@price_position_router.get('/price-position-dates/', summary='获取合约的时间跨度')
async def price_position_contract_dates(contract: str = Query(...)):
    with MySqlZ() as m_cursor:
        m_cursor.execute(
            "SELECT id, MIN(`date`) AS min_date, MAX(`date`) AS max_date "
            "FROM contribute_price_position "
            "WHERE contract=%s;",
            contract
        )
        result = m_cursor.fetchone()
    return {'message': '获取成功!', 'dates': result}


@price_position_router.get('/price-position/', summary='价格-持仓数据')
async def price_position(
        contract: str = Query(...),
        min_date: int = Query(...),
        max_date: int = Query(...)
):
    # 查询数据
    with MySqlZ() as m_cursor:
        m_cursor.execute(
            "SELECT id,`date`,variety_en,contract,close_price,empty_volume,long_position,short_position "
            "FROM contribute_price_position "
            "WHERE `date`>=%s AND `date`<=%s AND contract=%s;",
            (min_date, max_date, contract)
        )
        analysis_data = m_cursor.fetchall()

    # 转为DataFrame
    analysis_df = pd.DataFrame(
        analysis_data,
        columns=['id', 'date', 'variety_en', 'contract', 'close_price', 'empty_volume', 'long_position', 'short_position']
    )
    # 日期转为字符串
    analysis_df['date'] = analysis_df['date'].apply(lambda x: datetime.datetime.fromtimestamp(x).strftime('%Y%m%d'))
    # decimal数据类型转为float
    analysis_df['close_price'] = analysis_df['close_price'].apply(
        lambda x: int(x) if math.modf(x)[0] == 0 else round(x, 2))
    analysis_data = analysis_df.to_dict(orient='records')
    return {'message': '获取数据成功!', 'data': analysis_data}


