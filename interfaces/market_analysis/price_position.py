# _*_ coding:utf-8 _*_
# @File  : price_position.py
# @Time  : 2020-11-26 09:15
# @Author: zizle
import datetime
import math
import pandas as pd
from fastapi import APIRouter, Query, Body, Depends
from utils.verify import decipher_user_token, oauth2_scheme
from db.mysql_z import MySqlZ, ExchangeLibDB

"""
API-0: 生成指定日期价格-净持仓数据并入库保存
API-1: 获取价格持仓指定品种下的所有合约
API-2: 获取合约的时间跨度
API-3: 价格-持仓数据
"""


price_position_router = APIRouter()


def filter_items(item):
    # 过滤数据
    if 'EFP' in item['variety_en'].strip():
        return False
    else:
        return True


@price_position_router.post('/price-position/', summary='价格-净持率数据生成')
async def generate_price_position(option_day: str = Body(..., embed=True), user_token: str = Depends(oauth2_scheme)):
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
    # 读取每日的行情数据(收盘价,结算价,持仓量)
    # 和每日排名数据(多头,空头)
    with ExchangeLibDB() as ex_cursor:
        # 查询中金所的行情数据
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,close_price,settlement,empty_volume "
            "FROM cffex_daily "
            "WHERE `date`=%s;",
            (option_day,)
        )
        cffex_daily = ex_cursor.fetchall()
        # 查询郑商所的行情数据
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,close_price,settlement,empty_volume "
            "FROM czce_daily "
            "WHERE `date`=%s;",
            (option_day,)
        )
        czce_daily = ex_cursor.fetchall()
        # 查询大商所的行情数据
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,close_price,settlement,empty_volume "
            "FROM dce_daily "
            "WHERE `date`=%s;",
            (option_day,)
        )
        dce_daily = ex_cursor.fetchall()
        # 查询上期所的行情数据
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,close_price,settlement,empty_volume "
            "FROM shfe_daily "
            "WHERE `date`=%s;",
            (option_day,)
        )
        shfe_daily = ex_cursor.fetchall()
        all_daily = list(cffex_daily) + list(czce_daily) + list(dce_daily) + list(shfe_daily)
        # 转为数据框
        daily_df = pd.DataFrame(all_daily,
                                columns=['date', 'variety_en', 'contract', 'close_price', 'settlement', 'empty_volume'])
        # 查询日中金所排名合约统计
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,SUM(long_position) AS long_position,SUM(short_position) AS short_position "
            "FROM cffex_rank "
            "WHERE `date`=%s "
            "GROUP BY contract;",
            (option_day,)
        )
        cffex_rank = ex_cursor.fetchall()
        # 查询日郑商所排名合约统计
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,SUM(long_position) AS long_position,SUM(short_position) AS short_position "
            "FROM czce_rank "
            "WHERE `date`=%s AND contract<>variety_en "
            "GROUP BY contract;",
            (option_day,)
        )
        czce_rank = ex_cursor.fetchall()

        # 查询大商所排名合约统计
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,SUM(long_position) AS long_position,SUM(short_position) AS short_position "
            "FROM dce_rank "
            "WHERE `date`=%s "
            "GROUP BY contract;",
            (option_day,)
        )
        dce_rank = ex_cursor.fetchall()
        # 查询上期所排名合约统计
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,SUM(long_position) AS long_position,SUM(short_position) AS short_position "
            "FROM shfe_rank "
            "WHERE `date`=%s "
            "GROUP BY contract;",
            (option_day,)
        )
        shfe_rank = ex_cursor.fetchall()
        # 合并
        all_rank = list(cffex_rank) + list(czce_rank) + list(dce_rank) + list(shfe_rank)
        # 转为数据框
        rank_df = pd.DataFrame(all_rank, columns=['date', 'variety_en', 'contract', 'long_position', 'short_position'])
    # 合并数据框
    result_df = pd.merge(daily_df, rank_df, on=['date', 'variety_en', 'contract'], how='outer')
    # result_df = result_df.drop_duplicates(subset=['date', 'variety_en', 'contract'], keep='first')
    # 填写空值
    result_df = result_df.fillna(0)
    # date转为int时间戳
    # result_df['date'] = result_df['date'].apply(lambda x: int(datetime.datetime.strptime(x, '%Y%m%d').timestamp()))
    # 多空转为int
    result_df['long_position'] = result_df['long_position'].astype(int)
    result_df['short_position'] = result_df['short_position'].astype(int)
    # 数据转为dict入库
    save_items = result_df.to_dict(orient='records')
    save_items = list(filter(filter_items, save_items))
    # 将items保存入库
    if not save_items:
        return {"message": "没有查询到今日的持仓数据,无生成结果"}
    with ExchangeLibDB() as ex_cursor:
        count = ex_cursor.executemany(
            "INSERT INTO zero_price_position"
            "(`date`,variety_en,contract,close_price,settlement,empty_volume,long_position,short_position) "
            "VALUES (%(date)s,%(variety_en)s,%(contract)s,%(close_price)s,%(settlement)s,%(empty_volume)s,"
            "%(long_position)s,%(short_position)s);",
            save_items
        )
    return {"message": "保存{}价格-净持率数据成功!数量{}个".format(datetime.datetime.fromtimestamp(option_day).strftime('%Y-%m-%d'), count)}


@price_position_router.get('/price-position-contracts/', summary='获取品种价格持仓的所有合约')
async def price_position_contract(variety_en: str = Query(..., min_length=1, max_length=2)):
    with ExchangeLibDB() as ex_cursor:
        ex_cursor.execute(
            "SELECT id,contract "
            "FROM zero_price_position "
            "WHERE variety_en=%s "
            "GROUP BY contract "
            "ORDER BY contract DESC;",
            variety_en
        )
        all_contract = ex_cursor.fetchall()
    return {'message': '查询成功!', 'contracts': all_contract}


@price_position_router.get('/price-position-dates/', summary='获取合约的时间跨度')
async def price_position_contract_dates(contract: str = Query(...)):
    with ExchangeLibDB() as ex_cursor:
        ex_cursor.execute(
            "SELECT id, MIN(`date`) AS min_date, MAX(`date`) AS max_date "
            "FROM zero_price_position "
            "WHERE contract=%s;",
            contract
        )
        result = ex_cursor.fetchone()
    return {'message': '获取成功!', 'dates': result}


@price_position_router.get('/price-position/', summary='价格-持仓数据')
async def price_position(
        contract: str = Query(...),
        min_date: int = Query(...),
        max_date: int = Query(...)
):
    # 查询数据
    with ExchangeLibDB() as ex_cursor:
        ex_cursor.execute(
            "SELECT id,`date`,variety_en,contract,close_price,empty_volume,long_position,short_position "
            "FROM zero_price_position "
            "WHERE `date`>=%s AND `date`<=%s AND contract=%s;",
            (min_date, max_date, contract)
        )
        analysis_data = ex_cursor.fetchall()

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


