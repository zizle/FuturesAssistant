# _*_ coding:utf-8 _*_
# @File  : queryer.py
# @Time  : 2020-07-23 22:31
# @Author: zizle
import pandas as pd
from collections import OrderedDict
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException

from db.mysql_z import ExchangeLibDB

query_router = APIRouter()


async def verify_date(date: str = Query(...)):
    try:
        date = datetime.strptime(date, "%Y-%m-%d")
    except Exception:
        # 直接抛出异常即可
        raise HTTPException(status_code=400, detail="the query param `date` got an error format! must be `%Y-%m-%d`.")
    return date.strftime("%Y%m%d")


@query_router.get("/exchange/czce/daily/", summary="查询郑商所日行情数据")
async def query_czce_daily(query_date: str = Depends(verify_date)):
    query_sql = "SELECT * FROM `czce_daily` WHERE `date`=%s;" % query_date
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "id": "ID", "date": "日期", "variety_en": "品种", "contract": "合约", "pre_settlement": "前结算", "open_price": "开盘价", "highest": "最高价",
        "lowest": "最低价", "close_price": "收盘价", "settlement": "结算价","zd_1": "涨跌1", "zd_2": "涨跌2", "trade_volume": "成交量", "empty_volume": "空盘量",
        "increase_volume": "增减量", "trade_price": "成交额", "delivery_price": "交割结算价"
    })
    return {
        "message": "郑州商品交易所{}日交易行情数据查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }


@query_router.get("/exchange/czce/daily/variety-sum/", summary="查询郑商所日行情品种合计数据")
async def query_czce_daily_sum(query_date: str = Depends(verify_date)):
    query_sql = "SELECT `date`,variety_en,sum(trade_volume) as total_trade_volume," \
                "sum(empty_volume) as total_empty_volume, sum(increase_volume) as total_increase_volume " \
                "FROM `czce_daily` WHERE `date`=%s GROUP BY variety_en;" % query_date
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "date": "日期", "variety_en": "品种", "total_trade_volume": "成交量合计(手)",
        "total_empty_volume": "空盘量合计", "total_increase_volume": "增减量合计"
    })
    return {
        "message": "郑州商品交易所{}日行情统计查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }


@query_router.get("/exchange/czce/rank/", summary="查询郑商所日排名数据")
async def query_czce_rank(query_date: str = Depends(verify_date)):
    query_sql = "SELECT * FROM `czce_rank` WHERE `date`=%s;" % query_date
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "id": "ID", "date": "日期", "variety_en": "品种", "contract": "合约", "rank": "排名",
        "trade_company": "公司简称", "trade": "成交量", "trade_increase": "成交量增减",
        "long_position_company": "公司简称", "long_position": "持买仓量", "long_position_increase": "持买仓量增减",
        "short_position_company": "公司简称", "short_position": "持卖仓量", "short_position_increase": "持卖仓量增减"
    })
    return {
        "message": "郑州商品交易所{}日持仓排名数据查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }


@query_router.get("/exchange/czce/rank/variety-sum/", summary="查询郑商所日排名品种合计数据")
async def query_czce_rank_sum(query_date: str = Depends(verify_date), rank: int = Query(20, ge = 1, le = 20)):
    query_sql = "SELECT `date`,variety_en,contract," \
                "sum(trade) AS total_trade," \
                "sum(trade_increase) AS total_trade_increase," \
                "sum(long_position) AS total_long_position," \
                "sum(long_position_increase) AS total_long_position_increase," \
                "sum(short_position) AS total_short_position," \
                "sum(short_position_increase) AS total_short_position_increase," \
                "(sum(long_position) - sum(short_position)) AS net_position " \
                "FROM `czce_rank` WHERE `date`=%s AND `rank`<= %d GROUP BY contract;" % (query_date, rank)
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "date": "日期", "variety_en": "品种", "contract": "合约",
        "total_trade": "成交量合计", "total_trade_increase": "成交量增加合计",
        "total_long_position": "持买仓量合计", "total_long_position_increase": "持买仓量增减合计",
        "total_short_position": "持卖仓量合计", "total_short_position_increase": "持卖仓量增减合计",
        "net_position": "净持仓"
    })
    return {
        "message": "郑州商品交易所{}日持仓统计数据查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }


@query_router.get("/exchange/czce/receipt/", summary="查询郑商所仓单日报数据")
async def query_czce_receipt(query_date: str = Depends(verify_date)):
    query_sql = "SELECT * FROM `czce_receipt` WHERE `date`=%s;" % query_date
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "id": "ID", "date": "日期", "variety_en": "品种", "warehouse": "仓库简称", "receipt": "仓单数量",
        "receipt_increase": "仓单增减", "premium_discount": "升贴水"
    })
    return {
        "message": "郑州商品交易所{}仓单日报查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }


@query_router.get("/exchange/czce/receipt/variety-sum/", summary="查询郑商所仓单日报品种合计数据")
async def query_czce_receipt_sum(query_date: str = Depends(verify_date)):
    query_sql = "SELECT `date`,variety_en," \
                "sum(receipt) AS total_receipt, sum(receipt_increase) AS total_receipt_increase " \
                "FROM `czce_receipt` WHERE `date`=%s GROUP BY variety_en;" % query_date
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "date": "日期", "variety_en": "品种",
        "total_receipt": "仓单合计", "total_receipt_increase": "仓单增减",
    })

    return {
        "message": "郑州商品交易所{}每日仓单统计数据查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }


@query_router.get("/exchange/shfe/daily/", summary="查询上期所日行情数据")
async def query_shfe_daily(query_date: str = Depends(verify_date)):
    query_sql = "SELECT * FROM `shfe_daily` WHERE `date`=%s;" % query_date
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "id": "ID", "date": "日期", "variety_en": "品种", "contract": "合约", "pre_settlement": "前结算", "open_price": "开盘价", "highest": "最高价",
        "lowest": "最低价", "close_price": "收盘价", "settlement": "结算价", "zd_1": "涨跌1", "zd_2": "涨跌2", "trade_volume": "成交量", "empty_volume": "空盘量",
        "increase_volume": "增减量"
    })
    return {
        "message": "上海期货交易所{}日交易行情数据查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }


@query_router.get("/exchange/shfe/daily/variety-sum/", summary="查询上期所日行情品种合计数据")
async def query_shfe_daily_sum(query_date: str = Depends(verify_date)):
    query_sql = "SELECT `date`,variety_en,sum(trade_volume) as total_trade_volume," \
                "sum(empty_volume) as total_empty_volume, sum(increase_volume) as total_increase_volume " \
                "FROM `shfe_daily` WHERE `date`=%s GROUP BY variety_en;" % query_date
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "date": "日期", "variety_en": "品种", "total_trade_volume": "成交量合计(手)",
        "total_empty_volume": "空盘量合计", "total_increase_volume": "增减量合计"
    })
    return {
        "message": "上海期货交易所{}日行情统计查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }


@query_router.get("/exchange/shfe/rank/", summary="查询上期所日排名数据")
async def query_shfe_rank(query_date: str = Depends(verify_date)):
    query_sql = "SELECT * FROM `shfe_rank` WHERE `date`=%s;" % query_date
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "id": "ID", "date": "日期", "variety_en": "品种", "contract": "合约", "rank": "排名",
        "trade_company": "公司简称", "trade": "成交量", "trade_increase": "成交量增减",
        "long_position_company": "公司简称", "long_position": "持买仓量", "long_position_increase": "持买仓量增减",
        "short_position_company": "公司简称", "short_position": "持卖仓量", "short_position_increase": "持卖仓量增减"
    })
    return {
        "message": "上海期货交易所{}日持仓排名数据查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }


@query_router.get("/exchange/shfe/rank/variety-sum/", summary="查询上期所日排名品种合计数据")
async def query_shfe_rank_sum(query_date: str = Depends(verify_date), rank: int = Query(20, ge = 1, le = 20)):
    # 计算了前1名到自定义名次的品种持仓合计.rank=-1和0的期货公司.非期货公司不计算在内也不显示
    query_sql = "SELECT `date`,variety_en,contract," \
                "sum(trade) AS total_trade," \
                "sum(trade_increase) AS total_trade_increase," \
                "sum(long_position) AS total_long_position," \
                "sum(long_position_increase) AS total_long_position_increase," \
                "sum(short_position) AS total_short_position," \
                "sum(short_position_increase) AS total_short_position_increase," \
                "(sum(long_position) - sum(short_position)) AS net_position " \
                "FROM `shfe_rank` WHERE `date`=%s AND `rank`>=1 AND `rank`<= %d GROUP BY variety_en;" % (query_date, rank)
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "date": "日期", "variety_en": "品种",
        "total_trade": "成交量合计", "total_trade_increase": "成交量增加合计",
        "total_long_position": "持买仓量合计", "total_long_position_increase": "持买仓量增减合计",
        "total_short_position": "持卖仓量合计", "total_short_position_increase": "持卖仓量增减合计",
        "net_position": "净持仓"
    })

    return {
        "message": "上海期货交易所{}日持仓统计数据查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }


@query_router.get("/exchange/shfe/receipt/", summary="查询上期所仓单日报数据")
async def query_shfe_receipt(query_date: str = Depends(verify_date)):
    query_sql = "SELECT * FROM `shfe_receipt` WHERE `date`=%s;" % query_date
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "id": "ID", "date": "日期", "variety_en": "品种", "warehouse": "仓库简称", "receipt": "仓单数量",
        "receipt_increase": "仓单增减"
    })
    return {
        "message": "上海期货交易所{}仓单日报查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }


@query_router.get("/exchange/shfe/receipt/variety-sum/", summary="查询上期所仓单日报品种合计数据")
async def query_shfe_receipt_sum(query_date: str = Depends(verify_date)):
    query_sql = "SELECT `date`,variety_en," \
                "sum(receipt) AS total_receipt, sum(receipt_increase) AS total_receipt_increase " \
                "FROM `shfe_receipt` WHERE `date`=%s GROUP BY variety_en;" % query_date
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "date": "日期", "variety_en": "品种",
        "total_receipt": "仓单合计", "total_receipt_increase": "仓单增减",
    })

    return {
        "message": "上海期货交易所{}每日仓单统计数据查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }


@query_router.get("/exchange/cffex/daily/", summary="查询中金所日行情数据")
async def query_cffex_daily(query_date: str = Depends(verify_date)):
    query_sql = "SELECT * FROM `cffex_daily` WHERE `date`=%s;" % query_date
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "id": "ID", "date": "日期", "variety_en": "品种", "contract": "合约",
        "open_price": "开盘价", "highest": "最高价","lowest": "最低价", "close_price": "收盘价",
        "settlement": "结算价", "zd_1": "涨跌1", "zd_2": "涨跌2", "trade_volume": "成交量",
        "trade_price": "成交额", "empty_volume": "持仓量"
    })
    return {
        "message": "中国金融期货交易所{}日交易行情数据查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }


@query_router.get("/exchange/cffex/daily/variety-sum/", summary="查询中金所日行情品种合计数据")
async def query_cffex_daily_sum(query_date: str = Depends(verify_date)):
    query_sql = "SELECT `date`,variety_en," \
                "sum(trade_volume) as total_trade_volume,sum(trade_price) as total_trade_price, " \
                "sum(empty_volume) as total_empty_volume " \
                "FROM `cffex_daily` WHERE `date`=%s GROUP BY variety_en;" % query_date
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "date": "日期", "variety_en": "品种", "total_trade_volume": "成交量合计(手)",
        "total_trade_price": "成交额合计(万元)", "total_empty_volume": "持仓量量合计(手)"
    })
    return {
        "message": "中国金融交易所{}日行情统计查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }


@query_router.get("/exchange/cffex/rank/", summary="查询中金所日排名数据")
async def query_cffex_rank(query_date: str = Depends(verify_date)):
    query_sql = "SELECT * FROM `cffex_rank` WHERE `date`=%s;" % query_date
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "id": "ID", "date": "日期", "variety_en": "品种", "contract": "合约", "rank": "排名",
        "trade_company": "公司简称", "trade": "成交量", "trade_increase": "成交量增减",
        "long_position_company": "公司简称", "long_position": "持买仓量", "long_position_increase": "持买仓量增减",
        "short_position_company": "公司简称", "short_position": "持卖仓量", "short_position_increase": "持卖仓量增减"
    })
    return {
        "message": "中国金融期货交易所{}日持仓排名数据查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }


@query_router.get("/exchange/cffex/rank/variety-sum/", summary="查询中金所日排名品种合计数据")
async def query_cffex_rank_sum(query_date: str = Depends(verify_date), rank: int = Query(20, ge = 1, le = 20)):
    # 计算了前1名到自定义名次的品种持仓合计.rank=-1和0的期货公司.非期货公司不计算在内也不显示
    query_sql = "SELECT `date`,variety_en,contract," \
                "sum(trade) AS total_trade," \
                "sum(trade_increase) AS total_trade_increase," \
                "sum(long_position) AS total_long_position," \
                "sum(long_position_increase) AS total_long_position_increase," \
                "sum(short_position) AS total_short_position," \
                "sum(short_position_increase) AS total_short_position_increase," \
                "(sum(long_position) - sum(short_position)) AS net_position " \
                "FROM `cffex_rank` " \
                "WHERE `date`=%s AND `rank`>=1 AND `rank`<= %d " \
                "GROUP BY variety_en;" % (query_date, rank)
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "date": "日期", "variety_en": "品种",
        "total_trade": "成交量合计(手)", "total_trade_increase": "成交量增加合计",
        "total_long_position": "持买仓量合计(手)", "total_long_position_increase": "持买仓量增减合计",
        "total_short_position": "持卖仓量合计(手)", "total_short_position_increase": "持卖仓量增减合计",
        "net_position": "净持仓(手)"
    })
    return {
        "message": "中国金融期货交易所{}日持仓统计数据查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }


@query_router.get("/exchange/dce/daily/", summary="查询大商所日行情数据")
async def query_dce_daily(query_date: str = Depends(verify_date)):
    query_sql = "SELECT * FROM `dce_daily` WHERE `date`=%s;" % query_date
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "id": "ID", "date": "日期", "variety_en": "品种", "contract": "合约", "pre_settlement": "前结算",
        "open_price": "开盘价", "highest": "最高价","lowest": "最低价", "close_price": "收盘价",
        "settlement": "结算价", "zd_1": "涨跌1", "zd_2": "涨跌2", "trade_volume": "成交量",
        "trade_price": "成交额", "empty_volume": "持仓量", "increase_volume": "增减量"
    })
    return {
        "message": "大连商品交易所{}日交易行情数据查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }


@query_router.get("/exchange/dce/daily/variety-sum/", summary="查询大商所日行情品种合计数据")
async def query_dce_daily_sum(query_date: str = Depends(verify_date)):
    query_sql = "SELECT `date`,variety_en," \
                "sum(trade_volume) as total_trade_volume,sum(trade_price) as total_trade_price, " \
                "sum(empty_volume) as total_empty_volume,sum(increase_volume) as total_increase_volume " \
                "FROM `dce_daily` WHERE `date`=%s GROUP BY variety_en;" % query_date
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "date": "日期", "variety_en": "品种",
        "total_trade_volume": "成交量合计(手)", "total_trade_price": "成交额合计(万元)",
        "total_empty_volume": "持仓量量合计(手)", "total_increase_volume": "增减量合计"
    })
    return {
        "message": "大连商品交易所{}日行情统计查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }


@query_router.get("/exchange/dce/rank/", summary="查询大商所日排名数据")
async def query_dce_rank(query_date: str = Depends(verify_date)):
    query_sql = "SELECT * FROM `dce_rank` WHERE `date`=%s;" % query_date
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "id": "ID", "date": "日期", "variety_en": "品种", "contract": "合约", "rank": "排名",
        "trade_company": "公司简称", "trade": "成交量", "trade_increase": "成交量增减",
        "long_position_company": "公司简称", "long_position": "持买仓量", "long_position_increase": "持买仓量增减",
        "short_position_company": "公司简称", "short_position": "持卖仓量", "short_position_increase": "持卖仓量增减"
    })
    return {
        "message": "大连商品交易所{}日持仓排名数据查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }


@query_router.get("/exchange/dce/rank/variety-sum/", summary="查询大商所日排名品种合计数据")
async def query_dce_rank_sum(query_date: str = Depends(verify_date), rank: int = Query(20, ge = 1, le = 20)):
    query_sql = "SELECT `date`,variety_en,contract," \
                "sum(trade) AS total_trade," \
                "sum(trade_increase) AS total_trade_increase," \
                "sum(long_position) AS total_long_position," \
                "sum(long_position_increase) AS total_long_position_increase," \
                "sum(short_position) AS total_short_position," \
                "sum(short_position_increase) AS total_short_position_increase," \
                "(sum(long_position) - sum(short_position)) AS net_position " \
                "FROM `dce_rank` " \
                "WHERE `date`=%s AND `rank`>=1 AND `rank`<= %d " \
                "GROUP BY variety_en;" % (query_date, rank)
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "date": "日期", "variety_en": "品种",
        "total_trade": "成交量合计(手)", "total_trade_increase": "成交量增加合计",
        "total_long_position": "持买仓量合计(手)", "total_long_position_increase": "持买仓量增减合计",
        "total_short_position": "持卖仓量合计(手)", "total_short_position_increase": "持卖仓量增减合计",
        "net_position": "净持仓(手)"
    })
    return {
        "message": "大连商品交易所{}日持仓统计数据查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }


@query_router.get("/exchange/dce/receipt/", summary="查询大商所仓单日报数据")
async def query_dce_receipt(query_date: str = Depends(verify_date)):
    query_sql = "SELECT * FROM `dce_receipt` WHERE `date`=%s;" % query_date
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "id": "ID", "date": "日期", "variety_en": "品种", "warehouse": "仓库简称", "receipt": "仓单数量",
        "receipt_increase": "仓单增减"
    })
    return {
        "message": "大连商品交易所{}仓单日报查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }


@query_router.get("/exchange/dce/receipt/variety-sum/", summary="查询大商所仓单日报品种合计数据")
async def query_dce_receipt_sum(query_date: str = Depends(verify_date)):
    query_sql = "SELECT `date`,variety_en," \
                "sum(receipt) AS total_receipt, sum(receipt_increase) AS total_receipt_increase " \
                "FROM `dce_receipt` WHERE `date`=%s GROUP BY variety_en;" % query_date
    with ExchangeLibDB() as cursor:
        cursor.execute(query_sql)
        result = cursor.fetchall()
    keys = OrderedDict({
        "date": "日期", "variety_en": "品种",
        "total_receipt": "仓单合计", "total_receipt_increase": "仓单增减",
    })

    return {
        "message": "上海期货交易所{}每日仓单统计数据查询成功!".format(query_date),
        "result": result,
        "content_keys": keys
    }
