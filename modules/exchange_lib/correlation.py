# _*_ coding:utf-8 _*_
# @File  : correlation.py
# @Time  : 2021-03-04 15:11
# @Author: zizle
# 相关性分析
import datetime
import pandas as pd
from fastapi import APIRouter, Depends, Query, HTTPException
from db.mysql_z import ExchangeLibDB


corr_router = APIRouter()


def get_timestamp(ts: str = Query(...)):
    try:
        ts = int(datetime.datetime.strptime(ts, '%Y-%m-%d').timestamp())
    except ValueError:
        raise HTTPException(status_code=400, detail='ts or es can not format `%Y-%m-%d`')
    return ts


def get_end_timestamp(es: str = Query(...)):
    return get_timestamp(es)


@corr_router.get('/correlation/')
async def variety_correlation(ts: int = Depends(get_timestamp), es: int = Depends(get_end_timestamp)):
    print(ts, es)
    with ExchangeLibDB() as cursor:
        cursor.execute(
            'SELECT * FROM zero_price_index '
            'WHERE `date`>=%s AND `date`<=%s;',
            (ts, es)
        )
        price_data = cursor.fetchall()
    price_df = pd.DataFrame(price_data)
    if price_df.empty:
        return {'message': '查询成功!', 'correlation': []}
    # 以date分组提取各品种的dominant_price数据
    price_df['dominant_price'] = price_df['dominant_price'].astype(float)
    price_dfs = price_df.groupby(['date'])
    is_init_df = False
    result_df = None
    for pf in price_dfs:
        data_arr = pf[1].to_dict(orient='records')
        v_list, p_list = [], []
        for item in data_arr:
            v_list.append(item['variety_en'])
            p_list.append(item['dominant_price'])
        # 以v_list为列名,p_list为数据值DataFrame
        vp_df = pd.DataFrame([p_list], columns=v_list)
        if result_df is None:
            result_df = vp_df.copy()
        else:
            result_df = pd.concat([result_df, vp_df], axis=0)

    corr_df = result_df.corr()
    corr_df.fillna('-', inplace=True)
    return {'message': '查询成功!', 'correlation': corr_df.to_dict(orient='records')}
