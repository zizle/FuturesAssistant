# _*_ coding:utf-8 _*_
# @File  : exchange.py
# @Time  : 2021-06-30  14:24
# @Author: zizle
import datetime
import time

import numpy as np
import pandas as pd
from fastapi import APIRouter, Query, Depends, Body, Path
from db import FAConnection
from interfaces.depends import admin_logged_require, require_start_date, require_end_date
from status import r_status
from . import handler_pp

exchange_dsas_api = APIRouter()  # dsas: data set analysis system


# 查询指定日期的指数持仓数据(品种为查询参数,默认为None,无指定为全品种,指定时为该品种)
@exchange_dsas_api.get('/price-position/', summary='查询指定日期的指数持仓数据')
async def get_price_position(ds: datetime.datetime = Depends(require_start_date),
                             de: datetime.datetime = Depends(require_end_date),
                             c: str = Query(None, min_length=2, max_length=6)):
    db = FAConnection(conn_name='Query Price Position')
    if c:  # 指定合约(合约是品种时为主力合约)
        query_sql = 'SELECT quotes_ts,variety_en,contract,close_price,position_price,position_volume,' \
                    'long_position,short_position ' \
                    'FROM dat_futures_price_position WHERE quotes_ts>=%s AND quotes_ts<=%s AND contract=%s;'
        records = db.query(query_sql, [int(ds.timestamp()), int(de.timestamp()), c])
    else:  # 未指定，则查询所有指定合约
        query_sql = 'SELECT quotes_ts,variety_en,contract,close_price,position_price,position_volume,' \
                    'long_position,short_position ' \
                    'FROM dat_futures_price_position WHERE quotes_ts>=%s AND quotes_ts<=%s;'
        records = db.query(query_sql, [int(ds.timestamp()), int(de.timestamp())])
    df = pd.DataFrame(records)
    if df.empty:  # 没有数据
        if c:  # 指定合约时直接返回
            return {'code': r_status.SUCCESS, 'message': '查询指数与持仓数据为空!', 'data': [], 'enabled': True}
        # 未指定则查询原数据处理出数据
        ret_df = handler_pp.handle_price_position_with_source(ds)
        rep_data = ret_df.to_dict(orient='records')
        return {'code': r_status.SUCCESS, 'message': '查询指数与持仓数据成功!', 'data': rep_data, 'enabled': False}
    else:  # 有数据,则返回数据
        # 增加前20净持仓
        df['net_position'] = df['long_position'] - df['short_position']
        ret_df = handler_pp.handle_pp_display_format(df)
        rep_data = ret_df.to_dict(orient='records')
        return {'code': r_status.SUCCESS, 'message': '查询指数与持仓数据成功!', 'data': rep_data, 'enabled': True}


# 指定日期的指数持仓数据保存,需要后台用户登录
@exchange_dsas_api.post('/price-position/', summary='保存指定日期的指数持仓数据')
async def save_price_position(person: dict = Depends(admin_logged_require), pp_data: list = Body(...)):
    creator = person['uid']
    df = pd.DataFrame(pp_data)
    if df.empty:
        return {'code': r_status.CREATED_SUCCESS, 'message': '保存成功,未上传数据!'}
    del df['quotes_date']
    del df['net_position']
    df['close_price'] = df['close_price'].apply(lambda x: round(float(str(x).replace(',', '')), 3))
    df['position_price'] = df['position_price'].apply(lambda x: round(float(str(x).replace(',', '')), 3))
    df['position_volume'] = df['position_volume'].apply(lambda x: int(str(x).replace(',', '')))
    df['long_position'] = df['long_position'].apply(lambda x: int(str(x).replace(',', '')))
    df['short_position'] = df['short_position'].apply(lambda x: int(str(x).replace(',', '')))
    df['creator'] = [creator for _ in range(df.shape[0])]
    save_data = df.to_dict(orient='records')
    save_sql = 'INSERT IGNORE INTO dat_futures_price_position (creator,quotes_ts,variety_en,contract,close_price,' \
               'position_price,position_volume,long_position,short_position) ' \
               'VALUES (%(creator)s,%(quotes_ts)s,%(variety_en)s,%(contract)s,%(close_price)s,' \
               '%(position_price)s,%(position_volume)s,%(long_position)s,%(short_position)s);'
    db = FAConnection(conn_name='Save Price Position')
    count, _ = db.insert(save_sql, save_data, many=True)
    return {'code': r_status.CREATED_SUCCESS, 'message': f'保存成功,数量:{count}'}


# 指定品种年份区间数据查询(最大,最小,平均,当前年度值),extreme:极端,端点,pt:price type价格类型：dominant主力连续;weight:权重指数
@exchange_dsas_api.get('/iprice/year/extreme/', summary='指定年份分析最值区间的数据')  # ys: year start, ye: year end
async def quotes_extreme(ys: int = Query(..., ge=2003), ye: int = Query(..., ge=2004),
                         v: str = Query(..., min_length=1, max_length=2), pt: str = Query(...)):
    if ye <= ys:
        return {'code': r_status.VALIDATE_ERROR, 'message': 'param ye must greater than ys!'}
    if pt not in ['dominant', 'weight']:
        return {'code': r_status.VALIDATE_ERROR, 'message': 'param pt must as `dominant` or `weight`!'}
    start = datetime.datetime.strptime(f'{ys}-01-01', '%Y-%m-%d')
    end = datetime.datetime.strptime(f'{ye}-12-31', '%Y-%m-%d')
    cur_year = datetime.datetime.today().year
    cur_date = datetime.datetime.today().strftime('%m-%d')
    current = datetime.datetime.strptime(f'{cur_year}-01-01', '%Y-%m-%d')
    # 查询数据
    query_sql = 'SELECT quotes_ts,variety_en,close_price,position_price,position_volume ' \
                'FROM dat_futures_price_position ' \
                'WHERE variety_en=%s AND variety_en=contract AND ((quotes_ts>=%s AND quotes_ts<=%s) OR quotes_ts>=%s);'
    db = FAConnection(conn_name='Query Price Position')
    records = db.query(query_sql, [v.upper(), int(start.timestamp()), int(end.timestamp()), int(current.timestamp())])
    df = pd.DataFrame(records)
    if df.empty:
        return {'code': r_status.SUCCESS, 'message': '查询区间带绘图数据为空!', 'data': []}
    if pt == 'dominant':  # 查询的是主力收盘价
        df['price'] = df['close_price']
        del df['position_price']
        del df['position_volume']
    else:  # 查询的是权重价格
        df['price'] = df['position_price'] / df['position_volume']
        df['price'] = df['price'].apply(lambda x: round(x, 2))
    # 开始处理计算数据
    df['year'] = df['quotes_ts'].apply(lambda x: datetime.datetime.fromtimestamp(x).strftime('%Y'))
    df['month_date'] = df['quotes_ts'].apply(lambda x: datetime.datetime.fromtimestamp(x).strftime('%m-%d'))
    # 一年内所有的日期
    all_date = [[item.strftime('%m-%d')] for item in pd.date_range('2016-01-01', '2016-12-31').tolist()]  # 选择2016其为闰年
    date_df = pd.DataFrame(all_date, columns=['month_date'])  # 一年内所有的日期
    to_culdf = df[df['year'] <= str(ye)].copy()  # 计算的数据(年份小于当前年份的)
    current_df = df[df['year'] == str(cur_year)].copy()  # 当前年度的数据
    del df
    # 以年分组,循环每个dataframe,处理后横向拼接
    temp_df = pd.DataFrame()
    for year in to_culdf.groupby(by=['year'], as_index=False).groups:
        year_df = to_culdf[to_culdf['year'] == year]
        year_df = pd.merge(year_df, date_df, on='month_date', how='outer')  # 横向拼接
        year_df.sort_values(by=['month_date'], inplace=True)  # 排序
        year_df.fillna(method='ffill', inplace=True)  # 使用上值填充NAN
        year_df.fillna(method='bfill', inplace=True)  # 使用下方第一个非NAN填充(补充开年几天的数值)
        if year == str(cur_year):  # 当前年
            year_df = year_df[year_df['month_date'] <= cur_date]  # 当前年取到当前日期
        temp_df = pd.concat([temp_df, year_df])  # 竖向拼接

    temp_df.sort_values(by=['month_date', 'year'], inplace=True)  # 排序
    min_df = temp_df.groupby(by=['month_date'], as_index=False)['price'].min()
    max_df = temp_df.groupby(by=['month_date'], as_index=False)['price'].max()
    mean_df = temp_df.groupby(by=['month_date'], as_index=False)['price'].mean()

    # 横向拼接
    ret_df = pd.merge(min_df, max_df, on='month_date')
    ret_df.columns = ['month_date', 'min', 'max']
    ret_df = pd.merge(ret_df, mean_df, on='month_date')
    ret_df.columns = ['month_date', 'min', 'max', 'mean']

    ret_df = pd.merge(ret_df, current_df[['month_date', 'price']], on='month_date', how='left')  # 拼入当前年度数据
    ret_df['mean'] = ret_df['mean'].apply(lambda x: round(x, 2))
    ret_df.fillna(method='ffill', inplace=True)
    ret_df['price'] = ret_df['price'].mask(ret_df['month_date'] > cur_date, '-')  # 当前年度大于今日的数据处理
    ret_df.drop_duplicates(subset=['min', 'max', 'mean', 'price'], keep='last', inplace=True)
    ret_df.fillna('-', inplace=True)
    rep_data = ret_df.to_dict(orient='records')
    return {'code': r_status.SUCCESS, 'message': f'获取{ys}-{ye}最值区间图形数据成功!', 'data': rep_data}


# 全品种指定年区间涨跌振幅,源数据以pt参数指定
@exchange_dsas_api.get('/iprice/year/updown/', summary='指定年数全品种涨跌振幅')
async def quotes_year_up_down(ys: int = Query(..., ge=2003), ye: int = Query(..., ge=2004),
                              pt: str = Query(...)):
    if ye <= ys:
        return {'code': r_status.VALIDATE_ERROR, 'message': 'param ye must greater than ys!'}
    if pt not in ['dominant', 'weight']:
        return {'code': r_status.VALIDATE_ERROR, 'message': 'param pt must as `dominant` or `weight`!'}

    start = datetime.datetime.strptime(f'{ys - 1}-12-01', '%Y-%m-%d')
    end = datetime.datetime.strptime(f'{ye}-12-31', '%Y-%m-%d')
    query_sql = 'SELECT quotes_ts,variety_en,close_price,position_price,position_volume ' \
                'FROM dat_futures_price_position ' \
                'WHERE quotes_ts>=%s AND quotes_ts<=%s AND variety_en=contract;'
    db = FAConnection()
    records = db.query(query_sql, [int(start.timestamp()), int(end.timestamp())])
    df = pd.DataFrame(records)
    if df.empty:
        return {'code': r_status.SUCCESS, 'message': '全品种涨跌振幅查询为空!', 'data': []}
    if pt == 'dominant':  # 查询的是主力收盘价
        df['price'] = df['close_price']
        dat_explain = f'查询全品种{ys}年至{ye}年主力指数年度涨跌振幅数据成功!'
    else:  # 查询的是权重价格
        df['price'] = df['position_price'] / df['position_volume']
        df['price'] = df['price'].apply(lambda x: round(x, 2))
        dat_explain = f'查询全品种{ys}年至{ye}年权重指数年度涨跌振幅数据成功!'
    del df['position_price']
    del df['position_volume']
    df['year'] = df['quotes_ts'].apply(lambda x: datetime.datetime.fromtimestamp(x).strftime('%Y'))
    # 按年分组取最后一个
    last_df = df.groupby(by=['variety_en', 'year'], as_index=False).last()
    min_df = df.groupby(by=['variety_en', 'year'], as_index=False)['price'].min()
    max_df = df.groupby(by=['variety_en', 'year'], as_index=False)['price'].max()
    last_df.rename(columns={'price': 'last'}, inplace=True)
    min_df.rename(columns={'price': 'min'}, inplace=True)
    max_df.rename(columns={'price': 'max'}, inplace=True)
    # 合并数据框
    cul_df = pd.merge(last_df, min_df, on=['variety_en', 'year'])
    cul_df = pd.merge(cul_df, max_df, on=['variety_en', 'year'])
    # 品种分组计算
    ret_df = pd.DataFrame()
    for variety in cul_df.groupby(by=['variety_en']).groups:
        var_df = cul_df[cul_df['variety_en'] == variety].copy()
        # 计算涨跌 = (每年最后值 - 上年度最后值) / 上年度最后值
        var_df['zd'] = (var_df['last'] - var_df['last'].shift(1)) / var_df['last'].shift(1)
        # 计算振幅 = (每年最大值 - 每年最小值) / 每年最小值
        var_df['zf'] = (var_df['max'] - var_df['min']) / var_df['min']
        ret_df = pd.concat([ret_df, var_df])

    # 去掉第一行保留小数位
    ret_df = ret_df[ret_df['year'] >= str(ys)]
    ret_df['zd'] = ret_df['zd'].apply(lambda x: round(x, 4))
    ret_df['zf'] = ret_df['zf'].apply(lambda x: round(x, 4))
    ret_df.replace([np.inf, -np.inf], '-', inplace=True)
    ret_df.fillna('-', inplace=True)
    del ret_df['quotes_ts']
    rep_data = ret_df.to_dict(orient='records')
    return {'code': r_status.SUCCESS, 'message': dat_explain, 'data': rep_data}


# 全品种指定月的涨跌振幅,源数据为pt参数指定
@exchange_dsas_api.get('/iprice/month/updown/', summary='指定月全品种涨跌振幅')
async def quotes_month_up_down(month: int = Query(..., ge=1, le=12), pt: str = Query(...)):
    if pt not in ['dominant', 'weight']:
        return {'code': r_status.VALIDATE_ERROR, 'message': 'param pt must as `dominant` or `weight`!'}
    ascending = True  # 升序
    if month == 1:
        last_month = 12
        ascending = False  # 此时使用降序
    else:
        last_month = month - 1
    month_str, last_month_str = ('%02d' % month, '%02d' % last_month)
    # 查询数据
    query_sql = 'SELECT quotes_ts,variety_en,close_price,position_price,position_volume ' \
                'FROM dat_futures_price_position ' \
                'WHERE variety_en=contract AND ' \
                'FROM_UNIXTIME(quotes_ts,"%%m")=%s OR FROM_UNIXTIME(quotes_ts,"%%m")=%s;'
    db = FAConnection(conn_name='查询月涨跌')
    records = db.query(query_sql, [month_str, last_month_str])
    df = pd.DataFrame(records)
    if df.empty:
        return {'code': r_status.SUCCESS, 'message': '查询月份涨跌振幅为空!', 'data': []}
    if pt == 'dominant':  # 查询的是主力收盘价
        df['price'] = df['close_price']
        dat_explain = f'查询全品种全年度{month_str}月主力指数涨跌振幅成功!'
    else:  # 查询的是权重价格
        df['price'] = df['position_price'] / df['position_volume']
        df['price'] = df['price'].apply(lambda x: round(x, 2))
        dat_explain = f'查询全品种全年度{month_str}月权重指数涨跌振幅成功!'
    del df['close_price']
    del df['position_price']
    del df['position_volume']

    df['month'] = df['quotes_ts'].apply(lambda x: datetime.datetime.fromtimestamp(x).strftime('%Y-%m'))
    df['date'] = df['quotes_ts'].apply(lambda x: datetime.datetime.fromtimestamp(x).strftime('%Y-%m-%d'))
    df['year'] = df['quotes_ts'].apply(lambda x: datetime.datetime.fromtimestamp(x).strftime('%Y'))
    df.sort_values(by=['variety_en', 'month'], inplace=True, ascending=ascending)

    last_df = df.groupby(by=['variety_en', 'month'], as_index=False).last()
    min_df = df.groupby(by=['variety_en', 'month'], as_index=False)['price'].min()
    max_df = df.groupby(by=['variety_en', 'month'], as_index=False)['price'].max()
    last_df.rename(columns={'price': 'last'}, inplace=True)
    min_df.rename(columns={'price': 'min'}, inplace=True)
    max_df.rename(columns={'price': 'max'}, inplace=True)
    # 横向合并数据框
    cul_df = pd.merge(last_df, min_df, on=['variety_en', 'month'])
    cul_df = pd.merge(cul_df, max_df, on=['variety_en', 'month'])
    # 品种分组如果month的后2位等于当前请求月,则需要将其last值改为NAN
    default_variety = ''
    for row in range(cul_df.shape[0]):
        current_variety = cul_df.loc[row, 'variety_en']
        if current_variety != default_variety:
            default_variety = current_variety
            current_month = cul_df.loc[row, 'month']
            if current_month[-2:] == month_str:
                cul_df.loc[row, 'last'] = np.NAN
        else:
            continue

    # 由于上月为不要的数据，故无需分品种计算,
    # 计算涨跌 = (本月最后值 - 上月最后值) / 上月最后值
    cul_df['zd'] = (cul_df['last'] - cul_df['last'].shift(1)) / cul_df['last'].shift(1)
    # 计算振幅 = (本月最大值 - 本月最小值) / 本月最小值
    cul_df['zf'] = (cul_df['max'] - cul_df['min']) / cul_df['min']
    # 选取目标月份数据(去除上月数据,而且上月的zd数据会不准确刚好去除)
    cul_df['month_flag'] = cul_df['month'].apply(lambda x: x[-2:])
    cul_df = cul_df[cul_df['month_flag'] == month_str]
    cul_df['zd'] = cul_df['zd'].apply(lambda x: round(x, 4))
    cul_df['zf'] = cul_df['zf'].apply(lambda x: round(x, 4))
    # 处理nan与inf数据
    cul_df.replace([np.inf, -np.inf], '-', inplace=True)
    cul_df.fillna('-', inplace=True)
    ret_df = cul_df[['variety_en', 'month', 'min', 'max', 'zd', 'zf']].copy()
    rep_data = ret_df.to_dict(orient='records')
    return {'code': r_status.SUCCESS, 'message': dat_explain, 'data': rep_data}
