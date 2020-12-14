# _*_ coding:utf-8 _*_
# @File  : queryer.py
# @Time  : 2020-07-23 22:31
# @Author: zizle
import pandas as pd
from collections import OrderedDict
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from utils.constant import VARIETY_ZH

from db.mysql_z import ExchangeLibDB

query_router = APIRouter()


# 验证品种合法性
async def verify_date(date: str = Query(...)):
    try:
        date = datetime.strptime(date, "%Y-%m-%d")
    except Exception:
        # 直接抛出异常即可
        raise HTTPException(status_code=400, detail="the query param `date` got an error format! must be `%Y-%m-%d`.")
    return int(date.timestamp())


# 处理交易所的数据
def handler_exchange_data(data_df: pd.DataFrame, sort_by: list):
    # 排序
    table_df = data_df.sort_values(by=sort_by)
    # 添加中文列
    table_df['variety_zh'] = table_df['variety_en'].apply(lambda x: VARIETY_ZH.get(x, x))
    # 转日期
    table_df['date'] = table_df['date'].apply(lambda x: datetime.fromtimestamp(x).strftime('%Y-%m-%d'))
    # 转为字典
    return table_df.to_dict(orient='records')


@query_router.get("/exchange/cffex/daily/", summary="查询中金所日行情数据")
async def query_cffex_daily(query_date: int = Depends(verify_date), variety: str = Query('0')):
    with ExchangeLibDB() as cursor:
        cursor.execute(
            "SELECT * FROM `cffex_daily` WHERE `date`=%s AND IF('0'=%s,TRUE,variety_en=%s);",
            (query_date, variety, variety)
        )
        result = cursor.fetchall()
    # pandas处理数据
    table_df = pd.DataFrame(result, columns=['date', 'variety_en', 'contract', 'open_price', 'highest', 'lowest',
                                             'close_price', 'settlement', 'zd_1', 'zd_2', 'trade_volume', 'trade_price',
                                             'empty_volume'])
    table_values = handler_exchange_data(table_df, sort_by=['variety_en', 'contract'])
    keys = OrderedDict({
        "date": "日期", "variety_en": "品种", "contract": "合约",
        "open_price": "开盘价", "highest": "最高价","lowest": "最低价", "close_price": "收盘价",
        "settlement": "结算价", "zd_1": "涨跌1", "zd_2": "涨跌2", "trade_volume": "成交量",
        "trade_price": "成交额", "empty_volume": "持仓量"
    })
    return {
        "message": "中国金融期货交易所{}日交易行情数据查询成功!".format(query_date),
        "result": table_values,
        "content_keys": keys
    }


@query_router.get("/exchange/cffex/rank/", summary="查询中金所日排名数据")
async def query_cffex_rank(query_date: int = Depends(verify_date), variety: str = Query('0')):
    with ExchangeLibDB() as cursor:
        cursor.execute(
            "SELECT * FROM `cffex_rank` WHERE `date`=%s AND IF('0'=%s,TRUE,variety_en=%s);",
            (query_date, variety, variety)
        )
        result = cursor.fetchall()
    # pandas数据处理
    table_df = pd.DataFrame(result, columns=['date', 'variety_en', 'contract', 'rank',
                                             'trade_company', 'trade', 'trade_increase',
                                             'long_position_company', 'long_position', 'long_position_increase',
                                             'short_position_company', 'short_position', 'short_position_increase'])

    table_values = handler_exchange_data(table_df, sort_by=['variety_en', 'contract', 'rank'])
    keys = OrderedDict({
        "date": "日期", "variety_en": "品种", "contract": "合约", "rank": "排名",
        "trade_company": "公司简称", "trade": "成交量", "trade_increase": "成交量增减",
        "long_position_company": "公司简称", "long_position": "持买仓量", "long_position_increase": "持买仓量增减",
        "short_position_company": "公司简称", "short_position": "持卖仓量", "short_position_increase": "持卖仓量增减"
    })
    return {
        "message": "中国金融期货交易所{}日持仓排名数据查询成功!".format(query_date),
        "result": table_values,
        "content_keys": keys
    }


@query_router.get("/exchange/czce/daily/", summary="查询郑商所日行情数据")
async def query_czce_daily(query_date: int = Depends(verify_date), variety: str = Query('0')):
    with ExchangeLibDB() as cursor:
        cursor.execute(
            "SELECT * FROM `czce_daily` WHERE `date`=%s AND IF('0'=%s,TRUE,variety_en=%s);",
            (query_date, variety, variety)
        )
        result = cursor.fetchall()

    # pandas处理数据
    table_df = pd.DataFrame(result, columns=['date', 'variety_en', 'contract', 'pre_settlement', 'open_price', 'highest', 'lowest',
                                             'close_price', 'settlement', 'zd_1', 'zd_2', 'trade_volume',
                                             'increase_volume', 'trade_price', 'empty_volume', 'delivery_price'])
    table_values = handler_exchange_data(table_df, sort_by=['variety_en', 'contract'])
    keys = OrderedDict({
        "date": "日期", "variety_en": "品种", "contract": "合约", "pre_settlement": "前结算", "open_price": "开盘价", "highest": "最高价",
        "lowest": "最低价", "close_price": "收盘价", "settlement": "结算价","zd_1": "涨跌1", "zd_2": "涨跌2", "trade_volume": "成交量", "empty_volume": "空盘量",
        "increase_volume": "增减量", "trade_price": "成交额", "delivery_price": "交割结算价"
    })
    return {
        "message": "郑州商品交易所{}日交易行情数据查询成功!".format(query_date),
        "result": table_values,
        "content_keys": keys
    }


@query_router.get("/exchange/czce/rank/", summary="查询郑商所日排名数据")
async def query_czce_rank(query_date: str = Depends(verify_date), variety: str = Query('0')):
    with ExchangeLibDB() as cursor:
        cursor.execute(
            "SELECT * FROM `czce_rank` WHERE `date`=%s AND IF('0'=%s,TRUE,variety_en=%s);",
            (query_date, variety, variety)
        )
        result = cursor.fetchall()
    # pandas数据处理
    table_df = pd.DataFrame(result, columns=['date', 'variety_en', 'contract', 'rank',
                                             'trade_company', 'trade', 'trade_increase',
                                             'long_position_company', 'long_position', 'long_position_increase',
                                             'short_position_company', 'short_position', 'short_position_increase'])
    table_values = handler_exchange_data(table_df, sort_by=['variety_en', 'contract', 'rank'])
    keys = OrderedDict({
        "date": "日期", "variety_en": "品种", "contract": "合约", "rank": "排名",
        "trade_company": "公司简称", "trade": "成交量", "trade_increase": "成交量增减",
        "long_position_company": "公司简称", "long_position": "持买仓量", "long_position_increase": "持买仓量增减",
        "short_position_company": "公司简称", "short_position": "持卖仓量", "short_position_increase": "持卖仓量增减"
    })
    return {
        "message": "郑州商品交易所{}日持仓排名数据查询成功!".format(query_date),
        "result": table_values,
        "content_keys": keys
    }


@query_router.get("/exchange/dce/daily/", summary="查询大商所日行情数据")
async def query_dce_daily(query_date: str = Depends(verify_date), variety: str = Query('0')):
    with ExchangeLibDB() as cursor:
        cursor.execute(
            "SELECT * FROM `dce_daily` WHERE `date`=%s AND IF('0'=%s,TRUE,variety_en=%s);",
            (query_date, variety, variety)
        )
        result = cursor.fetchall()
    # pandas处理数据
    table_df = pd.DataFrame(result, columns=['date', 'variety_en', 'contract', 'pre_settlement', 'open_price', 'highest',
                                             'lowest', 'close_price', 'settlement', 'zd_1', 'zd_2', 'trade_volume',
                                             'trade_price', 'empty_volume', 'increase_volume'])
    table_values = handler_exchange_data(table_df, sort_by=['variety_en', 'contract'])
    keys = OrderedDict({
        "date": "日期", "variety_en": "品种", "contract": "合约", "pre_settlement": "前结算",
        "open_price": "开盘价", "highest": "最高价","lowest": "最低价", "close_price": "收盘价",
        "settlement": "结算价", "zd_1": "涨跌1", "zd_2": "涨跌2", "trade_volume": "成交量",
        "trade_price": "成交额", "empty_volume": "持仓量", "increase_volume": "增减量"
    })
    return {
        "message": "大连商品交易所{}日交易行情数据查询成功!".format(query_date),
        "result": table_values,
        "content_keys": keys
    }


@query_router.get("/exchange/dce/rank/", summary="查询大商所日排名数据")
async def query_dce_rank(query_date: str = Depends(verify_date), variety: str = Query('0')):
    with ExchangeLibDB() as cursor:
        cursor.execute(
            "SELECT * FROM `dce_rank` WHERE `date`=%s AND IF('0'=%s,TRUE,variety_en=%s);",
            (query_date, variety, variety)
        )
        result = cursor.fetchall()
    # pandas数据处理
    table_df = pd.DataFrame(result, columns=['date', 'variety_en', 'contract', 'rank',
                                             'trade_company', 'trade', 'trade_increase',
                                             'long_position_company', 'long_position', 'long_position_increase',
                                             'short_position_company', 'short_position', 'short_position_increase'])
    table_values = handler_exchange_data(table_df, sort_by=['variety_en', 'contract', 'rank'])
    keys = OrderedDict({
        "date": "日期", "variety_en": "品种", "contract": "合约", "rank": "排名",
        "trade_company": "公司简称", "trade": "成交量", "trade_increase": "成交量增减",
        "long_position_company": "公司简称", "long_position": "持买仓量", "long_position_increase": "持买仓量增减",
        "short_position_company": "公司简称", "short_position": "持卖仓量", "short_position_increase": "持卖仓量增减"
    })
    return {
        "message": "大连商品交易所{}日持仓排名数据查询成功!".format(query_date),
        "result": table_values,
        "content_keys": keys
    }


@query_router.get("/exchange/shfe/daily/", summary="查询上期所日行情数据")
async def query_shfe_daily(query_date: str = Depends(verify_date), variety: str = Query('0')):
    with ExchangeLibDB() as cursor:
        cursor.execute(
            "SELECT * FROM `shfe_daily` WHERE `date`=%s AND IF('0'=%s,TRUE,variety_en=%s);",
            (query_date, variety, variety)
        )
        result = cursor.fetchall()
    # pandas处理数据
    table_df = pd.DataFrame(result, columns=['date', 'variety_en', 'contract', 'pre_settlement', 'open_price', 'highest',
                                             'lowest', 'close_price', 'settlement', 'zd_1', 'zd_2', 'trade_volume',
                                             'empty_volume', 'increase_volume'])
    table_values = handler_exchange_data(table_df, sort_by=['variety_en', 'contract'])
    keys = OrderedDict({
        "date": "日期", "variety_en": "品种", "contract": "合约", "pre_settlement": "前结算", "open_price": "开盘价", "highest": "最高价",
        "lowest": "最低价", "close_price": "收盘价", "settlement": "结算价", "zd_1": "涨跌1", "zd_2": "涨跌2", "trade_volume": "成交量", "empty_volume": "空盘量",
        "increase_volume": "增减量"
    })
    return {
        "message": "上海期货交易所{}日交易行情数据查询成功!".format(query_date),
        "result": table_values,
        "content_keys": keys
    }


@query_router.get("/exchange/shfe/rank/", summary="查询上期所日排名数据")
async def query_shfe_rank(query_date: str = Depends(verify_date), variety: str = Query('0')):
    with ExchangeLibDB() as cursor:
        cursor.execute(
            "SELECT * FROM `shfe_rank` WHERE `date`=%s AND IF('0'=%s,TRUE,variety_en=%s);",
            (query_date, variety, variety)
        )
        result = cursor.fetchall()
    # pandas数据处理
    table_df = pd.DataFrame(result, columns=['date', 'variety_en', 'contract', 'rank',
                                             'trade_company', 'trade', 'trade_increase',
                                             'long_position_company', 'long_position', 'long_position_increase',
                                             'short_position_company', 'short_position', 'short_position_increase'])
    table_values = handler_exchange_data(table_df, sort_by=['variety_en', 'contract', 'rank'])
    keys = OrderedDict({
        "date": "日期", "variety_en": "品种", "contract": "合约", "rank": "排名",
        "trade_company": "公司简称", "trade": "成交量", "trade_increase": "成交量增减",
        "long_position_company": "公司简称", "long_position": "持买仓量", "long_position_increase": "持买仓量增减",
        "short_position_company": "公司简称", "short_position": "持卖仓量", "short_position_increase": "持卖仓量增减"
    })
    return {
        "message": "上海期货交易所{}日持仓排名数据查询成功!".format(query_date),
        "result": table_values,
        "content_keys": keys
    }
