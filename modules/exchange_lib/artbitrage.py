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
from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel
from db.mysql_z import MySqlZ, ExchangeLibDB
from utils.constant import SPOT_VARIETY_ZH
from utils.char_reverse import split_number_en

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


def unified_df_date(date_str, count):
    """ 以count为基准得到数据 """
    return date_str[:2] + '%02d' % (int(date_str[2:4]) + count) + date_str[4:]


@arbitrage_router.get('/arbitrage/contract-season/', summary='季节价差数据')
async def season_contract_arbitrage(
        v1: str = Query(...), v2: str = Query(...), c1: str = Query(...), c2: str = Query(...),
        year_count: int = Query(2)
):
    """
    套利计算：季节价差数据获取
    :param v1: 品种1
    :param v2: 品种2
    :param c1: 合约1
    :param c2: 合约2
    :param year_count: 追溯几年
    :return:
    """
    # 根据品种查询交易所,进而得到目标数据表
    table1, table2 = None, None
    with MySqlZ() as m_cursor:
        m_cursor.execute(
            "SELECT id,variety_name,exchange_lib FROM basic_variety WHERE variety_en=%s;",
            (v1,)
        )
        variety_item_1 = m_cursor.fetchone()
        m_cursor.execute(
            "SELECT id,variety_name,exchange_lib FROM basic_variety WHERE variety_en=%s;",
            (v2,)
        )
        variety_item_2 = m_cursor.fetchone()
        if variety_item_1:
            table1 = "{}_daily".format(variety_item_1["exchange_lib"])
        if variety_item_2:
            table2 = "{}_daily".format(variety_item_2["exchange_lib"])
    if not table1 or not table2:
        raise HTTPException(status_code=400, detail='variety error')
    # 分离合约的字母和数字,进而计算出需要的合约
    variety_en1, contract_num1 = split_number_en(c1)
    variety_en2, contract_num2 = split_number_en(c2)
    # print(contract_num1, contract_num2)
    contract1_list = []
    contract2_list = []
    for count in range(year_count):
        c1 = variety_en1 + str(int(contract_num1[:2]) - count) + contract_num1[2:]
        contract1_list.append(c1)
        c2 = variety_en2 + str(int(contract_num2[:2]) - count) + contract_num2[2:]
        contract2_list.append(c2)
    # 查询数据
    query_sql1 = "SELECT `date`,contract,close_price FROM {} WHERE contract IN {} ORDER BY `date`;".format(
        table1, str(tuple(contract1_list)))
    query_sql2 = "SELECT `date`,contract,close_price FROM {} WHERE contract IN {} ORDER BY `date`;".format(
        table2, str(tuple(contract2_list)))
    with ExchangeLibDB() as ex_cursor:
        ex_cursor.execute(query_sql1)
        contract_data1 = ex_cursor.fetchall()
        ex_cursor.execute(query_sql2)
        contract_data2 = ex_cursor.fetchall()
    # pandas处理数据
    contract1_df = pd.DataFrame(contract_data1)
    contract1_df.columns = ['date', 'contract1', 'closePrice1']
    contract2_df = pd.DataFrame(contract_data2)
    contract2_df.columns = ['date', 'contract2', 'closePrice2']

    # 跨越的日期区间
    min_date = '30001231'
    max_date = '19700101'

    # 目标数据容器
    target_values = {}
    count = -1
    for contract1, contract2 in zip(contract1_list, contract2_list):
        # print(contract1, contract2)
        value_key = '{}-{}'.format(contract1, contract2)
        # 截取数据
        df1 = contract1_df.loc[contract1_df['contract1'] == contract1]
        df2 = contract2_df.loc[contract2_df['contract2'] == contract2]
        # 计算年份的数量
        # print(contract1_df.groupby(['date']).count())
        # print(contract2_df.groupby(['date']).count())

        # 合并数据,计算需要的数据
        contract_df = pd.merge(df1, df2, on=['date'], how='outer')
        contract_df.dropna(axis=0, how='any', inplace=True)
        # # 选择价格>0的数
        contract_df = contract_df[(contract_df['closePrice1'] > 0) & (contract_df['closePrice2'] > 0)]
        if contract_df.empty:
            # target_values[value_key] = []
            continue
        # 以大合约为基准,从前一年的该月数据开始截取,截取后再转为同年份的横轴
        _, num_contract1 = split_number_en(contract1)
        _, num_contract2 = split_number_en(contract2)
        contract_year = max(num_contract1, num_contract2)
        # 取前两位-1得到起始的年,加后两位得到月 + '01' 得到起始日期
        # 取当前日期的年前2位，today
        current_year = str(datetime.datetime.today().year)[:2]
        # 截取数据的起始日期
        start_date = current_year + '%02d' % (int(contract_year[:2]) - 1) + contract_year[-2:] + '01'
        contract_df = contract_df[contract_df['date'] >= start_date]

        # 统一日期的年份
        contract_df['unified_date'] = contract_df['date'].apply(unified_df_date, args=(count, ))

        min_d = contract_df['unified_date'].min()
        max_d = contract_df['unified_date'].max()
        if min_d < min_date:
            min_date = min_d
        if max_d > max_date:
            max_date = max_d

        target_values[value_key] = contract_df.to_dict(orient='records')
        count += 1
    # 字典排序
    # print(target_values)
    # finally_data = OrderedDict()
    # for key in sorted(target_values.keys()):
    #     finally_data[key] = target_values[key]
    # print(target_values)
    return {'message': '查询季节性价差成功!', 'data': target_values, 'date_limit': [min_date, max_date]}


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

    # 查询品种1的合约数据
    query_sql1 = "SELECT `date`,close_price FROM {} WHERE contract=%s AND `date`>=%s AND `date`<=%s ORDER BY `date`;".format(
        table1)
    with ExchangeLibDB() as ex_cursor:
        # 查询品种1的合约数据
        ex_cursor.execute(query_sql1, (query_item.contract_1, start_date, end_date))
        contract_data1 = ex_cursor.fetchall()

        # 查询现货价格
        start_date = int(datetime.datetime.strptime(start_date, '%Y%m%d').timestamp())
        end_date = int(datetime.datetime.strptime(end_date, '%Y%m%d').timestamp())
        ex_cursor.execute(
            "SELECT `date`,price FROM zero_spot_price "
            "WHERE variety_en=%s AND `date`>=%s AND `date`<=%s ORDER BY `date`;",
            (query_item.variety_2, start_date, end_date)
        )
        spot_prices = ex_cursor.fetchall()
    if not spot_prices or not contract_data1:
        return {"message": "数据获取成功!", "data": [], "base_option": {'title': '目标无数据'}}

    # 处理数据
    df1 = pd.DataFrame(contract_data1)
    df1.columns = ["date", "closePrice1"]

    df2 = pd.DataFrame(spot_prices)
    df2.columns = ["date", "closePrice2"]
    # 将现货的date字段转为date
    df2['date'] = df2['date'].apply(lambda x: datetime.datetime.fromtimestamp(x).strftime('%Y%m%d'))
    data = data_frame_handler(df1, df2)
    # 图形需要的基础参数
    base_option = {
        "title": "期货{}-现货{}".format(variety1, SPOT_VARIETY_ZH.get(query_item.variety_2, query_item.variety_2)),
    }
    return {"message": "数据获取成功!", "data": data, "base_option": base_option}
