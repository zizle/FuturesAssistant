# _*_ coding:utf-8 _*_
# @File  : handler_pp.py
# @Time  : 2021-07-01  23:05
# @Author: zizle

import datetime
import pandas as pd
from db import FAConnection


# 处理指数和持仓价格的数据格式
def handle_pp_display_format(ret_df):
    ret_df['position_price'] = ret_df['position_price'].apply(lambda x: round(x, 3))
    ret_df['position_price'] = ret_df['position_price'].apply(
        lambda x: '{:,}'.format(x) if str(x).split('.')[1] > '0' else '{:,}'.format(int(x)))
    ret_df['position_volume'] = ret_df['position_volume'].apply(lambda x: '{:,}'.format(int(x)))
    ret_df['long_position'] = ret_df['long_position'].apply(lambda x: '{:,}'.format(int(x)))
    ret_df['short_position'] = ret_df['short_position'].apply(lambda x: '{:,}'.format(int(x)))
    ret_df['net_position'] = ret_df['net_position'].apply(lambda x: '{:,}'.format(int(x)))
    ret_df['quotes_date'] = ret_df['quotes_ts'].apply(lambda x: datetime.datetime.fromtimestamp(x).strftime('%Y-%m-%d'))
    return ret_df


# 处理品种的主力合约和持仓数据
def get_dominant_price_position(quotes_df, rank_df):
    # 品种分组取持仓量最大的数
    main_df = quotes_df.groupby(by=['variety_en'], as_index=False).apply(
        lambda x: x[x['position_volume'] == x['position_volume'].max()])
    # 再次品种分组取成交量大的数
    main_df = main_df.groupby(by=['variety_en'], as_index=False).apply(
        lambda x: x[x['trade_volume'] == x['trade_volume'].max()])
    # 品种合约排序,去重取第一个
    main_df.sort_values(by=['variety_en', 'contract'], inplace=True)
    main_df.drop_duplicates(subset=['quotes_ts', 'variety_en'], keep='first', inplace=True)  # 主力合约数据
    quotes_df['position_price'] = quotes_df['close_price'] * quotes_df['position_volume']  # 价格 * 持仓量
    # 品种分组求乘积和跟持仓量和
    sum_df = quotes_df.groupby(by=['variety_en'], as_index=False)[['position_price', 'position_volume']].sum()
    # 合并目标数据
    ret_quotes_df = pd.merge(main_df[['quotes_ts', 'variety_en', 'contract', 'close_price']], sum_df,
                             on='variety_en', how='left')
    del quotes_df
    del main_df
    del sum_df

    if rank_df.empty:
        ret_rank_df = pd.DataFrame()
    else:  # 处理出多单总量|空单总量
        # 取出variety_en==contract的数据,这是郑商所的数据，郑商所有直接公布品种排名
        czce_df = rank_df[rank_df['variety_en'] == rank_df['contract']]
        # 取出variety_en不在郑商所variety_en中的数据,这是其他交易所的数据
        czce_varieties = list(set(czce_df['variety_en'].tolist()))
        other_df = rank_df[~rank_df['variety_en'].isin(czce_varieties)]
        handle_df = pd.concat([czce_df, other_df])  # 上下拼接
        ret_rank_df = handle_df.groupby(by=['variety_en'], as_index=False).sum()  # 以品种分组求和
        del ret_rank_df['rank_ts']
    # 横向合并结果数据
    ret_df = pd.merge(ret_quotes_df, ret_rank_df, on='variety_en', how='left')
    # 将合约转为品种
    ret_df['contract'] = ret_df['variety_en']
    ret_df.fillna(0, inplace=True)
    return ret_df


# 处理各合约的数据
def get_contract_price_position(quotes_df, rank_df):
    # 加入position_price
    quotes_df['position_price'] = quotes_df['close_price'] * quotes_df['position_volume']
    quotes_df['position_price'] = quotes_df['position_price'].apply(lambda x: round(x, 3))
    # rank的合约计算
    # 取品种跟合约不相等的，去掉郑商所品种数据,算合约时不能有这个数据干扰
    exclude_czcev_df = rank_df[rank_df['variety_en'] != rank_df['contract']].copy()
    sum_rank = exclude_czcev_df.groupby(by=['variety_en', 'contract'], as_index=False).sum()
    # 合并
    ret_df = pd.merge(quotes_df, sum_rank, on=['variety_en', 'contract'], how='left')
    ret_df.dropna(subset=['long_position'], inplace=True)  # 去除无公布前20排名的合约
    del ret_df['trade_volume']
    del ret_df['rank_ts']
    return ret_df


# 查询行情及持仓数据处理出价格持仓数据
def handle_price_position_with_source(date: datetime.datetime):
    # 没有数据再使用源数据进行处理生成
    # (1)查询日行情数据
    sql_quotes = 'SELECT quotes_ts,variety_en,contract,close_price,trade_volume,position_volume ' \
                 'FROM dat_futures_daily_quotes WHERE quotes_ts=%s;'
    db = FAConnection(conn_name='源数据处理指数持仓')
    quotes_records = db.query(sql_quotes, [int(date.timestamp())], keep_conn=True)
    quotes_df = pd.DataFrame(quotes_records)
    # (2)查询日持仓数据
    sql_rank = 'SELECT rank_ts,variety_en,contract,rank,long_position,short_position ' \
               'FROM dat_futures_daily_rank WHERE rank_ts=%s;'
    rank_records = db.query(sql_rank, [int(date.timestamp())])
    rank_df = pd.DataFrame(rank_records)
    # (3)处理数据
    if quotes_df.empty:
        return pd.DataFrame()
    # 获取主力合约和前20持仓数据
    dominant_df = get_dominant_price_position(quotes_df.copy(), rank_df.copy())
    # 获取合约的持仓数据
    contract_df = get_contract_price_position(quotes_df, rank_df)
    final_df = pd.concat([dominant_df, contract_df])

    final_df['net_position'] = final_df['long_position'] - final_df['short_position']
    final_df.fillna(0, inplace=True)
    final_df = handle_pp_display_format(final_df)
    return final_df

