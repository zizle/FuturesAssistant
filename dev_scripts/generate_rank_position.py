# _*_ coding:utf-8 _*_
# @File  : generate_rank_position.py
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
    # 生成前一天
    pre_day = (datetime.fromtimestamp(query_date) + timedelta(days=-1)).strftime('%Y%m%d')
    query_date = int(datetime.strptime(pre_day, '%Y%m%d').timestamp())
    with ExchangeLibDB() as m_cursor:
        m_cursor.execute(
            "SELECT variety_en,long_position,short_position,net_position "
            "FROM zero_rank_position WHERE `date`=%s;", (query_date, )
        )
        date_data = m_cursor.fetchall()
        if not date_data:
            return query_preday(query_date)
        return date_data


# 查询和生成数据到数据库
def query_and_generate_to_lib(query_date):
    # 转为时间戳
    query_date = int(datetime.strptime(query_date.strftime("%Y%m%d"), '%Y%m%d').timestamp())
    # 获取当前最近一天前的数据(第一天的数据录入不用)
    pre_data = query_preday(query_date)
    # 转为dict
    pre_dict = {}
    for pre_item in pre_data:
        pre_dict[pre_item["variety_en"]] = pre_item
    # 查询四大交易所数据
    with ExchangeLibDB() as cursor:
        # 查询中金所品种持仓
        cursor.execute(
            "select `date`,variety_en,"
            "sum(long_position) as long_position,sum(short_position) as short_position "
            "from cffex_rank "
            "where date=%s and `rank`>=1 and `rank`<=20 "
            "group by variety_en;",
            (query_date, )
        )
        cffex_positions = cursor.fetchall()
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
        # # 查询大商所品种持仓
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
        save_items = list(cffex_positions) + list(czce_positions) + list(dce_positions) + list(shfe_positions)
        # save_items = list(czce_positions) + list(dce_positions) + list(shfe_positions)
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
        count = cursor.executemany(
            "INSERT INTO zero_rank_position (`date`,variety_en,"
            "long_position,long_position_increase,short_position,short_position_increase,"
            "net_position,net_position_increase) "
            "VALUES (%(date)s,%(variety_en)s,"
            "%(long_position)s,%(long_position_increase)s,%(short_position)s,%(short_position_increase)s,"
            "%(net_position)s,%(net_position_increase)s);",
            save_items
        )
        print("保存{}排名持仓和数据成功!数量{}个".format(datetime.fromtimestamp(query_date).strftime('%Y-%m-%d'), count))


if __name__ == '__main__':
    for op_date in date_generator("20020108", "20201211"):
        query_and_generate_to_lib(op_date)
        time.sleep(1)

