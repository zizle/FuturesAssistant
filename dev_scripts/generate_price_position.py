# _*_ coding:utf-8 _*_
# @File  : generate_price_position.py
# @Time  : 2020-11-24 16:09
# @Author: zizle
""" 生成合约的价格-净持率数据 """
import time
import datetime
import pandas as pd
from db.mysql_z import ExchangeLibDB, MySqlZ


# 生成日期函数
def date_generator(start, end):
    start = datetime.datetime.strptime(start, "%Y%m%d")
    end = datetime.datetime.strptime(end, "%Y%m%d")
    while start <= end:
        if start.weekday() < 5:
            yield start
        start += datetime.timedelta(days=1)


# 读取数据
def read_data(query_date):
    query_date = query_date.strftime("%Y%m%d")
    print("开始处理{}的数据.".format(query_date))
    # 读取每日的行情数据(收盘价,结算价,持仓量)
    # 和每日排名数据(多头,空头)
    with ExchangeLibDB() as ex_cursor:
        # 查询中金所的行情数据
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,close_price,settlement,empty_volume "
            "FROM cffex_daily "
            "WHERE `date`=%s;",
            (query_date, )
        )
        cffex_daily = ex_cursor.fetchall()
        # 查询郑商所的行情数据
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,close_price,settlement,empty_volume "
            "FROM czce_daily "
            "WHERE `date`=%s;",
            (query_date, )
        )
        czce_daily = ex_cursor.fetchall()
        # 查询大商所的行情数据
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,close_price,settlement,empty_volume "
            "FROM dce_daily "
            "WHERE `date`=%s;",
            (query_date,)
        )
        dce_daily = ex_cursor.fetchall()
        # 查询上期所的行情数据
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,close_price,settlement,empty_volume "
            "FROM shfe_daily "
            "WHERE `date`=%s;",
            (query_date,)
        )
        shfe_daily = ex_cursor.fetchall()
        all_daily = list(cffex_daily) + list(czce_daily) + list(dce_daily) + list(shfe_daily)
        # 转为数据框
        daily_df = pd.DataFrame(all_daily, columns=['date', 'variety_en', 'contract', 'close_price', 'settlement', 'empty_volume'])
        # 查询日中金所排名合约统计
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,SUM(long_position) AS long_position,SUM(short_position) AS short_position "
            "FROM cffex_rank "
            "WHERE `date`=%s "
            "GROUP BY contract;",
            (query_date, )
        )
        cffex_rank = ex_cursor.fetchall()
        # 查询日郑商所排名合约统计
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,SUM(long_position) AS long_position,SUM(short_position) AS short_position "
            "FROM czce_rank "
            "WHERE `date`=%s AND contract<>variety_en "
            "GROUP BY contract;",
            (query_date,)
        )
        czce_rank = ex_cursor.fetchall()

        # 查询大商所排名合约统计
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,SUM(long_position) AS long_position,SUM(short_position) AS short_position "
            "FROM dce_rank "
            "WHERE `date`=%s "
            "GROUP BY contract;",
            (query_date,)
        )
        dce_rank = ex_cursor.fetchall()
        # 查询上期所排名合约统计
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,SUM(long_position) AS long_position,SUM(short_position) AS short_position "
            "FROM shfe_rank "
            "WHERE `date`=%s "
            "GROUP BY contract;",
            (query_date,)
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
    result_df['date'] = result_df['date'].apply(lambda x: int(datetime.datetime.strptime(x, '%Y%m%d').timestamp()))
    # 多空转为int
    result_df['long_position'] = result_df['long_position'].astype(int)
    result_df['short_position'] = result_df['short_position'].astype(int)
    # 数据转为dict入库
    return result_df.to_dict(orient='records')


def filter_items(item):
    # 过滤数据
    if 'EFP' in item['variety_en'].strip():
        return False
    else:
        return True


def save_data(items):
    # items.pop(-1)
    items = list(filter(filter_items, items))
    print(len(items))
    # for item in items:
    #     print(item)
    if not items:
        print("数据为空!")
        return
    with MySqlZ() as m_cursor:
        count = m_cursor.executemany(
            "INSERT INTO contribute_price_position"
            "(`date`,variety_en,contract,close_price,settlement,empty_volume,long_position,short_position) "
            "VALUES (%(date)s,%(variety_en)s,%(contract)s,%(close_price)s,%(settlement)s,%(empty_volume)s,"
            "%(long_position)s,%(short_position)s);",
            items
        )
    print("增加{}个数据.".format(count))
    # for item in items:
    #     print(item)
    # print(len(items))


if __name__ == '__main__':
    for op_date in date_generator('20201101', '20201109'):
        result = read_data(op_date)
        save_data(result)
        # print(int(op_date.timestamp()))
        # print(datetime.datetime.fromtimestamp(int(op_date.timestamp())).strftime("%Y-%m-%d"))
        time.sleep(1)


