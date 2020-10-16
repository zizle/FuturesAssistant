# _*_ coding:utf-8 _*_
# @File  : position.py
# @Time  : 2020-08-21 12:55
# @Author: zizle

""" 持仓相关 """
from datetime import datetime, timedelta
from fastapi import APIRouter, Query
from pandas import DataFrame, pivot_table, concat
from db.mysql_z import ExchangeLibDB
from utils.constant import VARIETY_ZH

position_router = APIRouter()


DCE_VARIETY_EN = ['A', 'B', 'C', 'CS', 'EB', 'EG', 'I', 'J', 'JD', 'JM', 'L', 'M', 'P', 'PG', 'PP', 'RR', 'V', 'Y']
CZCE_VARIETY_EN = ['AP', 'CF', 'CJ', 'CY', 'FG', 'JR', 'LR', 'MA', 'OI', 'PF', 'PM', 'RI', 'RM', 'RS', 'SA', 'SF', 'SM',
                   'SR', 'TA', 'UR', 'WH', 'ZC']
SHFE_VARIETY_EN = ['AG', 'AL', 'AU', 'BU', 'CU', 'FU', 'HC', 'LU', 'NI', 'NR', 'PB', 'RB',
                   'RU', 'SN', 'SP', 'SS', 'ZN']
CFFEX_VARIETY_EN = ['IC', 'IF', 'IH', 'T', 'TF', 'TS']


def pivot_data_frame(source_df, exchange_lib):
    """ 透视转表数据 """
    source_df["net_position"] = source_df["net_position"].astype(int)
    pivot_df = pivot_table(source_df, index=["variety_en"], columns=["date"])
    # 检测不存在的品种插入插入行,数据为nan
    if exchange_lib == 'dce':
        pivot_df = pivot_df.reindex(DCE_VARIETY_EN, axis="rows")
    elif exchange_lib == 'czce':
        pivot_df = pivot_df.reindex(CZCE_VARIETY_EN, axis="rows")
    elif exchange_lib == 'shfe':
        pivot_df = pivot_df.reindex(SHFE_VARIETY_EN, axis="rows")
    elif exchange_lib == 'cffex':
        pivot_df = pivot_df.reindex(CFFEX_VARIETY_EN, axis="rows")
    else:
        pass
    return pivot_df


def get_variety_zh(variety_en):
    """ 获取交易代码的对应中文 """
    return VARIETY_ZH.get(variety_en, variety_en)


@position_router.get('/position/all-variety/', summary='全品种净持仓数据')
async def all_variety_net_position(interval_days: int = Query(1)):
    # 获取当前日期及45天前
    current_date = datetime.today()
    pre_date = current_date + timedelta(days=-45)
    start_date = pre_date.strftime('%Y%m%d')
    end_date = current_date.strftime('%Y%m%d')
    with ExchangeLibDB() as cursor:
        # 查询大商所的品种净持仓
        cursor.execute(
            "select `date`,variety_en,(sum(long_position) - sum(short_position)) as net_position "
            "from dce_rank "
            "where date<=%s and date>=%s and `rank`>=1 and `rank`<=20 "
            "group by `date`,variety_en;",
            (end_date, start_date)
        )
        dce_net_positions = cursor.fetchall()

        # 查询郑商所的品种净持仓
        cursor.execute(
            "select `date`,variety_en,(sum(long_position) - sum(short_position)) as net_position "
            "from czce_rank "
            "where date<=%s and date>=%s and `rank`>=1 and `rank`<=20  and variety_en=contract "
            "group by `date`,variety_en;",
            (end_date, start_date)
        )
        czce_net_positions = cursor.fetchall()

        # 查询上期所的品种净持仓
        cursor.execute(
            "select `date`,variety_en,(sum(long_position) - sum(short_position)) as net_position "
            "from shfe_rank "
            "where date<=%s and date>=%s and `rank`>=1 and `rank`<=20 "
            "group by `date`,variety_en;",
            (end_date, start_date)
        )
        shfe_net_positions = cursor.fetchall()

        # 查询中金所的品种净持仓
        cursor.execute(
            "select `date`,variety_en,(sum(long_position) - sum(short_position)) as net_position "
            "from cffex_rank "
            "where date<=%s and date>=%s and `rank`>=1 and `rank`<=20 "
            "group by `date`,variety_en;",
            (end_date, start_date)
        )
        cffex_net_positions = cursor.fetchall()

    # 处理各交易所的数据
    dce_df = DataFrame(dce_net_positions)
    czce_df = DataFrame(czce_net_positions)
    shfe_df = DataFrame(shfe_net_positions)
    cffex_df = DataFrame(cffex_net_positions)

    all_variety_df = concat(
        [pivot_data_frame(dce_df, 'dce'), pivot_data_frame(czce_df, 'czce'), pivot_data_frame(shfe_df, 'shfe'), pivot_data_frame(cffex_df, 'cffex')]
    )
    # 倒置列顺序
    all_variety_df = all_variety_df.iloc[:, ::-1]
    # 间隔取数
    split_df = all_variety_df.iloc[:, ::interval_days]
    # 整理表头
    split_df.columns = split_df.columns.droplevel(0)
    split_df = split_df.reset_index()
    split_df = split_df.fillna(0)
    # 处理顺序(按字母排序)
    split_df.sort_values(by='variety_en', inplace=True)
    # 增加中文列
    split_df["variety_zh"] = split_df["variety_en"].apply(get_variety_zh)
    data_dict = split_df.to_dict(orient='records')
    header_keys = split_df.columns.values.tolist()
    header_keys.remove("variety_zh")  # 删除中文标签
    header_keys[0] = "variety_zh"  # 第一个改为中文
    final_data = dict()
    for item in data_dict:
        final_data[item['variety_en']] = item

    return {"message": "查询全品种净持仓数据成功!", "data": final_data, 'header_keys': header_keys}

