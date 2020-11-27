# _*_ coding:utf-8 _*_
# @File  : price_index.py
# @Time  : 2020-11-27 08:34
# @Author: zizle
""" 价格指数API
API-1: 品种下的时间跨度

"""
import math
import datetime
import pandas as pd
from fastapi import APIRouter, Query
from db.mysql_z import MySqlZ

price_index_router = APIRouter()


@price_index_router.get('/price-index-dates/', summary='品种下的时间跨度')
async def variety_price_index_dates(variety_en: str = Query(...)):
    with MySqlZ() as m_cursor:
        m_cursor.execute(
            "SELECT id, MIN(`date`) AS min_date, MAX(`date`) AS max_date "
            "FROM contribute_price_index "
            "WHERE variety_en=%s;",
            variety_en
        )
        result = m_cursor.fetchone()
    return {'message': '获取成功!', 'dates': result}


@price_index_router.get('/price-index/', summary='价格指数数据')
async def price_index(
        variety_en: str = Query(...),
        min_date: int = Query(...),
        max_date: int = Query(...)
):
    # 查询数据
    with MySqlZ() as m_cursor:
        m_cursor.execute(
            "SELECT id,`date`,variety_en,total_position,total_trade,dominant_price,weight_price "
            "FROM contribute_price_index "
            "WHERE `date`>=%s AND `date`<=%s AND variety_en=%s;",
            (min_date, max_date, variety_en)
        )
        analysis_data = m_cursor.fetchall()
    # 转为DataFrame
    analysis_df = pd.DataFrame(
        analysis_data,
        columns=['id', 'date', 'variety_en', 'total_position', 'total_trade', 'dominant_price',
                 'weight_price']
    )
    # 日期转为字符串
    analysis_df['date'] = analysis_df['date'].apply(lambda x: datetime.datetime.fromtimestamp(x).strftime('%Y%m%d'))
    # decimal数据类型转为float
    analysis_df['dominant_price'] = analysis_df['dominant_price'].apply(
        lambda x: int(x) if math.modf(x)[0] == 0 else round(x, 2))
    analysis_df['weight_price'] = analysis_df['weight_price'].apply(
        lambda x: int(x) if math.modf(x)[0] == 0 else round(x, 2))
    analysis_data = analysis_df.to_dict(orient='records')
    base_option = {
        'title': '{}的{}价格指数'.format(variety_en, '{}')
    }
    return {'message': '获取数据成功!', 'data': analysis_data, 'base_option': base_option}