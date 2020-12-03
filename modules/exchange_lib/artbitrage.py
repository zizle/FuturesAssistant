# _*_ coding:utf-8 _*_
# @File  : artbitrage.py
# @Time  : 2020-11-17 15:36
# @Author: zizle

""" 套利计算
API-1: 查询两个品种指定日期的价格数据
API-2: 查询期货现货的价格数据
"""
import datetime
import pandas as pd
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
from db.mysql_z import MySqlZ, ExchangeLibDB
from utils.constant import SPOT_VARIETY_ZH

arbitrage_router = APIRouter()


def df_zero_handler(num):
    try:
        if int(num) == 0:
            return '-'
    except Exception:
        return '-'
    else:
        return num


def data_frame_handler(df1, df2):
    """ 处理2个数据框的数据 """
    contract_df = pd.merge(df1, df2, on=["date"], how="outer")
    # 填空值
    contract_df.fillna('-', inplace=True)
    # 处理0值
    contract_df['closePrice1'] = contract_df['closePrice1'].apply(df_zero_handler)
    contract_df['closePrice2'] = contract_df['closePrice2'].apply(df_zero_handler)
    # 排序
    contract_df.sort_values('date', inplace=True)
    # 转为字典
    return contract_df.to_dict(orient="records")


class ArbitrageItem(BaseModel):
    variety_1: str
    variety_2: str
    contract_1: str
    contract_2: str
    day_count: int = 90


@arbitrage_router.post("/arbitrage/variety/", summary="跨品种套利计算(含跨期套利)")
async def arbitrage_variety(query_item: ArbitrageItem = Body(...)):
    # 分别查询品种所在的交易所
    table1, table2 = None, None
    # 根据当前日期计算出日期
    today = datetime.datetime.today()
    start_date = (today + datetime.timedelta(days=-query_item.day_count)).strftime('%Y%m%d')
    end_date = today.strftime('%Y%m%d')
    with MySqlZ() as m_cursor:
        m_cursor.execute(
            "SELECT id,variety_name,exchange_lib FROM basic_variety WHERE variety_en=%s;",
            (query_item.variety_1,)
        )
        variety_item_1 = m_cursor.fetchone()
        m_cursor.execute(
            "SELECT id,variety_name,exchange_lib FROM basic_variety WHERE variety_en=%s;",
            (query_item.variety_2,)
        )
        variety_item_2 = m_cursor.fetchone()
        if variety_item_1:
            table1 = "{}_daily".format(variety_item_1["exchange_lib"])
        if variety_item_2:
            table2 = "{}_daily".format(variety_item_2["exchange_lib"])
    if not table1 or not table2:
        raise HTTPException(status_code=400, detail='variety error')
    # 查询品种的合约数据
    query_sql1 = "SELECT `date`,close_price FROM {} WHERE contract=%s AND `date`>=%s AND `date`<=%s ORDER BY `date`;".format(
        table1)
    query_sql2 = "SELECT `date`,close_price FROM {} WHERE contract=%s AND `date`>=%s AND `date`<=%s ORDER BY `date`;".format(
        table2)
    with ExchangeLibDB() as ex_cursor:
        ex_cursor.execute(query_sql1, (query_item.contract_1, start_date, end_date))
        contract_data1 = ex_cursor.fetchall()
        ex_cursor.execute(query_sql2, (query_item.contract_2, start_date, end_date))
        contract_data2 = ex_cursor.fetchall()
    # 处理数据
    df1 = pd.DataFrame(contract_data1)
    df1.columns = ["date", "closePrice1"]

    df2 = pd.DataFrame(contract_data2)
    df2.columns = ["date", "closePrice2"]
    data = data_frame_handler(df1, df2)
    # 图形需要的基础参数
    base_option = {
        "title": "{}-{}".format(query_item.contract_1, query_item.contract_2),
    }
    return {"message": "数据获取成功!", "data": data, "base_option": base_option}


@arbitrage_router.post("/arbitrage/futures-spot/", summary="期现套利计算")
async def arbitrage_variety(query_item: ArbitrageItem = Body(...)):
    # 查询品种1所在的交易所
    table1 = None
    variety1 = ""
    # 根据当前日期计算出日期
    today = datetime.datetime.today()
    start_date = (today + datetime.timedelta(days=-query_item.day_count)).strftime('%Y%m%d')
    end_date = today.strftime('%Y%m%d')
    with MySqlZ() as m_cursor:
        m_cursor.execute(
            "SELECT id,variety_name,exchange_lib FROM basic_variety WHERE variety_en=%s;", (query_item.variety_1,)
        )
        variety_item_1 = m_cursor.fetchone()
        if variety_item_1:
            table1 = "{}_daily".format(variety_item_1["exchange_lib"])
            variety1 = variety_item_1["variety_name"]
        if not table1:
            raise HTTPException(status_code=400, detail='variety error')
        # 查询现货价格
        m_cursor.execute(
            "SELECT `date`,spot_price FROM industry_spot_price "
            "WHERE variety_en=%s AND `date`>=%s AND `date`<=%s ORDER BY `date`;",
            (query_item.variety_2, start_date, end_date)
        )
        spot_prices = m_cursor.fetchall()
    # 查询品种1的合约数据
    query_sql1 = "SELECT `date`,close_price FROM {} WHERE contract=%s AND `date`>=%s AND `date`<=%s ORDER BY `date`;".format(
        table1)
    with ExchangeLibDB() as ex_cursor:
        ex_cursor.execute(query_sql1, (query_item.contract_1, start_date, end_date))
        contract_data1 = ex_cursor.fetchall()

    # 处理数据
    df1 = pd.DataFrame(contract_data1)
    df1.columns = ["date", "closePrice1"]

    df2 = pd.DataFrame(spot_prices)
    df2.columns = ["date", "closePrice2"]
    data = data_frame_handler(df1, df2)
    # 图形需要的基础参数
    base_option = {
        "title": "{}-{}".format(variety1, SPOT_VARIETY_ZH.get(query_item.variety_2, query_item.variety_2)),
    }
    return {"message": "数据获取成功!", "data": data, "base_option": base_option}
