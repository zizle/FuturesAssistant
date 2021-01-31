# _*_ coding:utf-8 _*_

# 添加2021年1月投顾策略
import datetime
import pandas as pd
from db.mysql_z import MySqlZ


def date_converter(column_content):
    if isinstance(column_content, datetime.datetime):
        return int(column_content.timestamp())
    else:
        raise ValueError('日期有误')


def read_records():
    strategy_df = pd.read_excel('投顾策略1月份xxx.xlsx', converters={1: date_converter})
    strategy_df['update_time'] = strategy_df['create_time']
    strategy_df['author_id'] = [0 for _ in range(strategy_df.shape[0])]
    records = strategy_df.to_dict(orient='records')
    with MySqlZ() as cursor:
        cursor.executemany(
            "INSERT INTO product_strategy(create_time,update_time,content,author_id) "
            "VALUES(%(create_time)s,%(update_time)s,%(content)s,%(author_id)s)",
            records
        )





if __name__ == '__main__':
    read_records()