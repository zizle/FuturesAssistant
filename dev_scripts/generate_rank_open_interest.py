# _*_ coding:utf-8 _*_
# @File  : generate_rank_open_interest.py
# @Time  : 2020-11-11 08:39
# @Author: zizle
""" 生成前20名净持仓的数据 """
import time
from datetime import datetime, timedelta
from pandas import DataFrame, concat, pivot_table
from db.mysql_z import ExchangeLibDB, MySqlZ


# 生成日期函数
def date_generator(start, end):
    start = datetime.strptime(start, "%Y%m%d")
    end = datetime.strptime(end, "%Y%m%d")
    while start <= end:
        if start.weekday() < 5:
            yield start
        start += timedelta(days=1)


def query_preday(query_date):
    query_date = (query_date + timedelta(days=-1)).strftime("%Y%m%d")
    with MySqlZ() as m_cursor:
        m_cursor.execute(
            "SELECT variety_en,long_position,short_position,net_position "
            "FROM exchange_rank_holding WHERE `date`=%s;", (query_date, )
        )
        date_data = m_cursor.fetchall()
        if not date_data:
            return query_preday(datetime.strptime(query_date, "%Y%m%d"))
        return date_data


# 查询和生成数据到数据库
def query_and_generate_to_lib(query_date):
    # # 获取当前最近一天前的数据(第一天的数据录入不用)
    pre_data = query_preday(query_date)
    # 转为dict
    pre_dict = {}
    for pre_item in pre_data:
        pre_dict[pre_item["variety_en"]] = pre_item

    # pre_dict = {} # 第一天的数据录入不用

    # for k,v in pre_dict.items():
    #     print(k,v)
    query_date = query_date.strftime("%Y%m%d")
    # 查询四大交易所数据
    with ExchangeLibDB() as cursor:
        # 查询中金所品种持仓
        # cursor.execute(
        #     "select `date`,variety_en,"
        #     "sum(long_position) as long_position,sum(short_position) as short_position "
        #     "from cffex_rank "
        #     "where date=%s and `rank`>=1 and `rank`<=20 "
        #     "group by variety_en;",
        #     (query_date, )
        # )
        # cffex_positions = cursor.fetchall()
        # 查询郑商所品种持仓
        cursor.execute(
            "select `date`,variety_en,"
            "sum(long_position) as long_position,sum(short_position) as short_position "
            "from czce_rank "
            "where date=%s and `rank`>=1 and `rank`<=20 and variety_en=contract "
            "group by variety_en;",
            (query_date, )
        )
        czce_positions = cursor.fetchall()
        # 查询大商所品种持仓
        cursor.execute(
            "select `date`,variety_en,"
            "sum(long_position) as long_position,sum(short_position) as short_position "
            "from dce_rank "
            "where date=%s and `rank`>=1 and `rank`<=20 "
            "group by variety_en;",
            (query_date,)
        )
        dce_positions = cursor.fetchall()
        # 查询上期所持仓
        cursor.execute(
            "select `date`,variety_en,"
            "sum(long_position) as long_position,sum(short_position) as short_position "
            "from shfe_rank "
            "where date=%s and `rank`>=1 and `rank`<=20 "
            "group by variety_en;",
            (query_date,)
        )
        shfe_positions = cursor.fetchall()

    # 合并以上查询的结果
    # save_items = list(cffex_positions) + list(czce_positions) + list(dce_positions) + list(shfe_positions)
    save_items = list(czce_positions) + list(dce_positions) + list(shfe_positions)
    # print("="*100)
    # 转换数据类型
    for item in save_items:
        item["long_position"] = int(item["long_position"])
        item["short_position"] = int(item["short_position"])
        item["net_position"] = item["long_position"] - item["short_position"]
        pre_day = pre_dict.get(item["variety_en"])
        if pre_day:
            item["long_position_increase"] = item["long_position"] - pre_day["long_position"]
            item["short_position_increase"] = item["short_position"] - pre_day["short_position"]
            item["net_position_increase"] = item["net_position"] - pre_day["net_position"]
        else:
            item["long_position_increase"] = item["long_position"]
            item["short_position_increase"] = item["short_position"]
            item["net_position_increase"] = item["net_position"]
        # print(item)

    # 将items保存入库
    if not save_items:
        print("没有{}的数据!".format(query_date))
        return
    with MySqlZ() as m_cursor:
        count = m_cursor.executemany(
            "INSERT INTO exchange_rank_holding (`date`,variety_en,"
            "long_position,long_position_increase,short_position,short_position_increase,"
            "net_position,net_position_increase) "
            "VALUES (%(date)s,%(variety_en)s,"
            "%(long_position)s,%(long_position_increase)s,%(short_position)s,%(short_position_increase)s,"
            "%(net_position)s,%(net_position_increase)s);",
            save_items
        )
    print("保存{}排名持仓和数据成功!数量{}个".format(query_date, count))


if __name__ == '__main__':
    for op_date in date_generator("20070101", "20071231"):
        query_and_generate_to_lib(op_date)
        time.sleep(1)
