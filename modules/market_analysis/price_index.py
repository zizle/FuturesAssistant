# _*_ coding:utf-8 _*_
# @File  : price_index.py
# @Time  : 2020-11-27 08:34
# @Author: zizle
""" 价格指数API
API-0: 生成指数数据
API-1: 品种下的时间跨度
API-2: 价格指数数据

"""
import math
import datetime
import pandas as pd
from fastapi import APIRouter, Query, Body, Depends
from utils.verify import oauth2_scheme, decipher_user_token
from db.mysql_z import MySqlZ, ExchangeLibDB

price_index_router = APIRouter()


def filter_items(item):
    # 过滤数据
    if 'EFP' in item['variety_en'].strip():
        return False
    else:
        return True


@price_index_router.post('/price-index/', summary='生成价格指数数据')
async def generate_price_index(option_day: str = Body(..., embed=True), user_token: str = Depends(oauth2_scheme)):
    # 验证日期格式
    try:
        option_day = int(datetime.datetime.strptime(option_day, "%Y%m%d").timestamp())
    except Exception:
        return {"message": "日期格式有误!"}
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        return {"message": "暂无权限操作或登录过期"}
    # 验证用户身份
    with MySqlZ() as m_cursor:
        m_cursor.execute("SELECT id,role FROM user_user WHERE id=%s;", (user_id,))
        user_info = m_cursor.fetchone()
        if not user_info or user_info["role"] not in ["superuser", "operator"]:
            return {"message": "暂无权限操作"}
    # 进行数据生成
    # 读取各交易所的日行情数据并进性处理
    with ExchangeLibDB() as ex_cursor:
        # 查询中金所的日行情数据
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,close_price,empty_volume,trade_volume "
            "FROM cffex_daily "
            "WHERE `date`=%s;",
            (option_day,)
        )
        cffex_daily = ex_cursor.fetchall()
        # 查询郑商所得日行情数据
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,close_price,empty_volume,trade_volume "
            "FROM czce_daily "
            "WHERE `date`=%s;",
            (option_day,)
        )
        czce_daily = ex_cursor.fetchall()
        # 查询大商所得日行情数据
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,close_price,empty_volume,trade_volume "
            "FROM dce_daily "
            "WHERE `date`=%s;",
            (option_day,)
        )
        dce_daily = ex_cursor.fetchall()
        # 查询上期所得日行情数据
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,close_price,empty_volume,trade_volume "
            "FROM shfe_daily "
            "WHERE `date`=%s;",
            (option_day,)
        )
        shfe_daily = ex_cursor.fetchall()
    # 加和
    all_daily = list(cffex_daily) + list(czce_daily) + list(dce_daily) + list(shfe_daily)
    if not all_daily:
        return {"message": "没有查询到今日的数据,无生成结果"}
    # 转为数据框
    daily_df = pd.DataFrame(all_daily,
                            columns=['date', 'variety_en', 'contract', 'close_price', 'empty_volume', 'trade_volume'])
    # 增加收盘价 * 持仓的结果列
    daily_df['closePriceEmptyVolume'] = daily_df['close_price'] * daily_df['empty_volume']
    # 转数据类型(decimal在求和时无法求出)
    daily_df['close_price'] = daily_df['close_price'].astype(float)
    daily_df['closePriceEmptyVolume'] = daily_df['closePriceEmptyVolume'].astype(float)
    # for i in daily_df.itertuples():
    #     print(i)
    # print('=' * 50)
    # 分组得到最大持仓量(主力合约)
    dominant_df = daily_df.groupby('variety_en').apply(lambda x: x[x.empty_volume == x.empty_volume.max()])
    # 如果最大持仓量相同则根据成交量去重
    dominant_df.index = dominant_df.index.droplevel(0)  # 删除一个索引
    # 再次分组取成交量大的(持仓量一致会导致重复的去重操作)
    dominant_df = dominant_df.groupby('variety_en').apply(lambda x: x[x.trade_volume == x.trade_volume.max()])
    # 取值
    dominant_df = dominant_df[['date', 'close_price']].reset_index()
    dominant_df = dominant_df[['date', 'variety_en', 'close_price']]
    # 分组求和(计算权重价格)
    weight_df = daily_df.groupby('variety_en').sum().reset_index()
    # 计算权重价格
    weight_df['weight_price'] = round(weight_df['closePriceEmptyVolume'] / weight_df['empty_volume'], 2)
    # 取值
    weight_df = weight_df[['variety_en', 'weight_price', 'empty_volume', 'trade_volume']]
    # 合并所需数据
    result_df = pd.merge(dominant_df, weight_df, on=['variety_en'], how='inner')
    # 填充空值
    result_df = result_df.fillna(0)
    # 重置index
    result_df.columns = ['date', 'variety_en', 'dominant_price', 'weight_price', 'total_position', 'total_trade']
    # date转为int时间戳
    # result_df['date'] = result_df['date'].apply(lambda x: int(datetime.datetime.strptime(x, '%Y%m%d').timestamp()))
    # 去重
    result_df.drop_duplicates(inplace=True)
    # 还是重复继续去重
    result_df.drop_duplicates(subset=['date', 'variety_en'], keep='first', inplace=True)
    save_items = result_df.to_dict(orient='records')
    save_items = list(filter(filter_items, save_items))
    # 保存入库
    if not save_items:
        return {"message": "没有查询到今日的数据,无生成结果"}
    with ExchangeLibDB() as ex_cursor:
        count = ex_cursor.executemany(
            "INSERT INTO zero_price_index"
            "(`date`,variety_en,total_position,total_trade,dominant_price,weight_price) "
            "VALUES (%(date)s,%(variety_en)s,%(total_position)s,%(total_trade)s,%(dominant_price)s,%(weight_price)s);",
            save_items
        )
    return {"message": "保存{}指数数据成功!数量{}个".format(datetime.datetime.fromtimestamp(option_day).strftime('%Y-%m-%d'), count)}


@price_index_router.get('/price-index-dates/', summary='品种下的时间跨度')
async def variety_price_index_dates(variety_en: str = Query(...)):
    with ExchangeLibDB() as ex_cursor:
        ex_cursor.execute(
            "SELECT id, MIN(`date`) AS min_date, MAX(`date`) AS max_date "
            "FROM zero_price_index "
            "WHERE variety_en=%s;",
            variety_en
        )
        result = ex_cursor.fetchone()
    return {'message': '获取成功!', 'dates': result}


@price_index_router.get('/price-index/', summary='价格指数数据')
async def price_index(
        variety_en: str = Query(...),
        min_date: int = Query(...),
        max_date: int = Query(...)
):
    # 查询数据
    with ExchangeLibDB() as ex_cursor:
        ex_cursor.execute(
            "SELECT id,`date`,variety_en,total_position,total_trade,dominant_price,weight_price "
            "FROM zero_price_index "
            "WHERE `date`>=%s AND `date`<=%s AND variety_en=%s "
            "ORDER BY `date`;",
            (min_date, max_date, variety_en)
        )
        analysis_data = ex_cursor.fetchall()
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