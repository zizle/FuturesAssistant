# _*_ coding:utf-8 _*_
# @File  : migrate_spot_price.py
# @Time  : 2021-07-14 15:52
# @Author: zizle


# 迁移现货报价数据
import time
import datetime
from db import FAConnection
import pandas as pd


def get_spot_price(ts):
    db = FAConnection()
    records = db.query('SELECT id,date,variety_en,price FROM zero_spot_price WHERE `date`=%s;', [ts])
    return pd.DataFrame(records)


def date_generator(start, end):
    start_date = datetime.datetime.strptime(start, '%Y-%m-%d')
    end_date = datetime.datetime.strptime(end, '%Y-%m-%d')
    while start_date <= end_date:
        yield int(start_date.timestamp())
        start_date += datetime.timedelta(days=1)


def start_migrate():
    for d in date_generator('2021-07-11', '2021-07-13'):
        df = get_spot_price(d)
        if df.empty:
            continue
        df['price'] = df['price'].astype(float)
        df['creator'] = [1 for _ in range(df.shape[0])]
        df['spot_ts'] = df['date']
        df['src_note'] = ['' for _ in range(df.shape[0])]
        del df['date']
        # print(df)
        save_spot_price(df.to_dict(orient='records'), d)
        time.sleep(0.6)


def save_spot_price(save_data, ts):
    # 保存数据
    save_sql = 'INSERT IGNORE INTO dat_spot_price (creator,spot_ts,variety_en,' \
               'price,src_note) ' \
               'VALUES (%(creator)s,%(spot_ts)s,%(variety_en)s,' \
               '%(price)s,%(src_note)s);'

    db = FAConnection(conn_name='Save Spots')
    count, _ = db.insert(save_sql, param=save_data, many=True)

    print(f'保存 {datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")} 现货价格完成,{count}个。')


if __name__ == '__main__':
    start_migrate()
