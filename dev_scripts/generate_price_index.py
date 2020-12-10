# _*_ coding:utf-8 _*_
# @File  : generate_price_index.py
# @Time  : 2020-11-25 14:01
# @Author: zizle
""" 生成品种权重价格指数和主力合约价格指数表 """
import time
import pandas as pd
import datetime
from db.mysql_z import ExchangeLibDB, MySqlZ


# 生成日期函数
def date_generator(start, end):
    start = datetime.datetime.strptime(start, "%Y%m%d")
    end = datetime.datetime.strptime(end, "%Y%m%d")
    while start <= end:
        if start.weekday() < 5:
            yield start
        start += datetime.timedelta(days=1)


def read_data(query_date):
    query_date = datetime.datetime.strftime(query_date, '%Y%m%d')
    print("开始处理{}的价格指数数据.".format(query_date))
    # 读取各交易所的日行情数据并进性处理
    with ExchangeLibDB() as ex_cursor:
        # # 查询中金所的日行情数据
        # ex_cursor.execute(
        #     "SELECT `date`,variety_en,contract,close_price,empty_volume,trade_volume "
        #     "FROM cffex_daily "
        #     "WHERE `date`=%s;",
        #     (query_date, )
        # )
        # cffex_daily = ex_cursor.fetchall()
        # 查询郑商所得日行情数据
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,close_price,empty_volume,trade_volume "
            "FROM czce_daily "
            "WHERE `date`=%s;",
            (query_date, )
        )
        czce_daily = ex_cursor.fetchall()
        # 查询大商所得日行情数据
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,close_price,empty_volume,trade_volume "
            "FROM dce_daily "
            "WHERE `date`=%s;",
            (query_date,)
        )
        dce_daily = ex_cursor.fetchall()
        # 查询上期所得日行情数据
        ex_cursor.execute(
            "SELECT `date`,variety_en,contract,close_price,empty_volume,trade_volume "
            "FROM shfe_daily "
            "WHERE `date`=%s;",
            (query_date,)
        )
        shfe_daily = ex_cursor.fetchall()
    # 加和
    # all_daily = list(cffex_daily) + list(czce_daily) + list(dce_daily) + list(shfe_daily)
    all_daily = list(czce_daily) + list(dce_daily) + list(shfe_daily)
    if not all_daily:
        return {}
    # 转为数据框
    daily_df = pd.DataFrame(all_daily, columns=['date', 'variety_en', 'contract', 'close_price', 'empty_volume', 'trade_volume'])
    # 增加收盘价 * 持仓的结果列
    daily_df['closePriceEmptyVolume'] = daily_df['close_price'] * daily_df['empty_volume']
    # 转数据类型(decimal在求和时无法求出)
    daily_df['close_price'] = daily_df['close_price'].astype(float)
    daily_df['closePriceEmptyVolume'] = daily_df['closePriceEmptyVolume'].astype(float)
    # for i in daily_df.itertuples():
    #     print(i)
    # print('=' * 50)
    # 分组得到最大持仓量(主力合约)
    dominant_df = daily_df.groupby('variety_en').apply(lambda x: x[x.empty_volume == x.empty_volume.max()])
    dominant_df.index = dominant_df.index.droplevel(0)  # 删除一个索引
    # 再次分组取成交量大的(持仓量一致会导致重复的去重操作)# 如果最大持仓量相同则根据成交量去重
    dominant_df = dominant_df.groupby('variety_en').apply(lambda x: x[x.trade_volume == x.trade_volume.max()])
    # 取值
    dominant_df = dominant_df[['date', 'close_price']].reset_index()
    dominant_df = dominant_df[['date', 'variety_en', 'close_price']]
    # 分组求和(计算权重价格)
    weight_df = daily_df.groupby('variety_en').sum().reset_index()
    # 计算权重价格
    weight_df['weight_price'] = round(weight_df['closePriceEmptyVolume'] / weight_df['empty_volume'], 2)
    # 取值
    weight_df = weight_df[['variety_en', 'weight_price', 'empty_volume', 'trade_volume']]
    # 合并所需数据
    result_df = pd.merge(dominant_df, weight_df, on=['variety_en'], how='inner')
    # 填充空值
    result_df = result_df.fillna(0)
    # 重置index
    result_df.columns = ['date', 'variety_en', 'dominant_price', 'weight_price', 'total_position', 'total_trade']
    # date转为int时间戳
    result_df['date'] = result_df['date'].apply(lambda x: int(datetime.datetime.strptime(x, '%Y%m%d').timestamp()))
    # 去重
    result_df.drop_duplicates(inplace=True)
    # 还是重复继续去重
    result_df.drop_duplicates(subset=['date', 'variety_en'], keep='first', inplace=True)
    return result_df.to_dict(orient='records')


def filter_items(item):
    # 过滤数据
    if 'EFP' in item['variety_en'].strip():
        return False
    else:
        return True

def save_data(items):
    if not items:
        print("数据为空!")
        return
    # for i in items:
    #     print(i)
    items = list(filter(filter_items, items))
    with ExchangeLibDB() as m_cursor:
        count = m_cursor.executemany(
            "INSERT INTO zero_price_index"
            "(`date`,variety_en,total_position,total_trade,dominant_price,weight_price) "
            "VALUES (%(date)s,%(variety_en)s,%(total_position)s,%(total_trade)s,%(dominant_price)s,%(weight_price)s);",
            items
        )
    print("增加{}个数据.".format(count))


if __name__ == '__main__':
    for op_date in date_generator('20060101', '20091231'):
        result = read_data(op_date)
        save_data(result)
        # save_data(result)
        # print(int(op_date.timestamp()))
        # print(datetime.datetime.fromtimestamp(int(op_date.timestamp())).strftime("%Y-%m-%d"))
        time.sleep(1)
