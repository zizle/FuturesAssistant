# _*_ coding:utf-8 _*_
# @File  : weekly.py
# @Time  : 2020-12-23 13:09
# @Author: zizle

""" 周度涨跌数据
1. 净持仓和权重指数周度涨跌数据
"""
import datetime
import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from db.mysql_z import ExchangeLibDB
from utils.constant import VARIETY_ZH


weekly_router = APIRouter()


# 验证日期的函数
def verify_date(date: str):
    try:
        date = datetime.datetime.strptime(date, '%Y%m%d')
    except ValueError:
        raise HTTPException(status_code=400, detail='param `date` does not match format `%Y%m%d`')
    return date


# 1. 净持仓和权重指数周度涨跌数据
@weekly_router.get('/position-weight-price/', summary='净持仓-权重指数周度涨跌')
async def position_weight_price(date=Depends(verify_date)):
    this_monday = date + datetime.timedelta(days=-date.weekday())  # 本周一
    current_date = int(date.timestamp())  # 请求的日期

    last_monday = int((this_monday + datetime.timedelta(days=-7)).timestamp())  # 上周一
    last_sunday = int((this_monday + datetime.timedelta(days=-1)).timestamp())  # 上周日
    # 查询数据、
    execute_sql = "SELECT * FROM zero_price_index WHERE " \
                  "`date`=(SELECT MAX(`date`) FROM zero_price_position WHERE `date`>=%s AND `date`<=%s);"
    with ExchangeLibDB() as ex_cursor:
        # last week
        ex_cursor.execute(execute_sql, (last_monday, last_sunday))
        last_week_data = ex_cursor.fetchall()
        # this week
        ex_cursor.execute(execute_sql, (this_monday, current_date))
        current_week_data = ex_cursor.fetchall()
    # 处理数据
    # 转为DataFrame
    last_week_df = pd.DataFrame(
        last_week_data,
        columns=['date', 'variety_en', 'total_position', 'weight_price', 'dominant_price']
    )
    # 重新设置列索引
    last_week_df.columns = ['l_date', 'variety_en', 'l_position', 'l_price', 'l_dominant_price']

    current_week_df = pd.DataFrame(
        current_week_data,
        columns=['date', 'variety_en', 'total_position', 'weight_price', 'dominant_price']
    )
    # 重新设置列索引
    current_week_df.columns = ['c_date', 'variety_en', 'c_position', 'c_price', 'c_dominant_price']

    # 合并数据
    data_df = pd.merge(last_week_df, current_week_df, how='inner', on='variety_en')

    # 计算持仓涨跌幅度
    data_df['position_increase'] = (data_df['c_position'] - data_df['l_position']) / data_df['l_position']
    # 转化数据类型
    data_df[['l_price', 'c_price']] = data_df[['l_price', 'c_price']].astype(float)
    # 计算权重价格涨跌幅度
    data_df['wp_increase'] = (data_df['c_price'] - data_df['l_price']) / data_df['l_price']
    # 得到上周日期和当周日期
    l_date = datetime.datetime.fromtimestamp(data_df['l_date'][0]).strftime('%Y-%m-%d')
    c_date = datetime.datetime.fromtimestamp(data_df['c_date'][0]).strftime('%Y-%m-%d')
    # 截取需要的数据
    data_df = data_df[['variety_en', 'l_position', 'c_position', 'position_increase', 'wp_increase']]
    # 选取不含inf和nan的行
    data_df = data_df[~data_df.isin([np.nan, np.inf]).any(1)]
    # 按持仓增减幅度降序
    data_df = data_df.sort_values(by='position_increase', ascending=False)
    # 去除指定品种
    data_df = data_df[~data_df[['variety_en']].isin(['JR', 'RR']).any(1)]
    # 增加品种中文列
    data_df['variety_name'] = data_df['variety_en'].apply(lambda x: VARIETY_ZH.get(x, x))
    return {'last_date': l_date, 'current_date': c_date, 'data': data_df.to_dict(orient='records')}

