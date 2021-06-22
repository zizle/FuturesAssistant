# _*_ coding:utf-8 _*_
# @File  : handler_contract_price.py
# @Time  : 2021-06-16 15:26
# @Author: zizle


# 查询合约数据生成csv文件
import datetime
import pandas as pd


from db.mysql_z import ExchangeLibDB


pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)


def read_db():
    with ExchangeLibDB() as cursor:
        cursor.execute('SELECT date,variety_en,dominant_price FROM zero_price_index;')
        records = cursor.fetchall()
        df = pd.DataFrame(records)
        return df


def read_spot_price():
    with ExchangeLibDB() as cursor:
        cursor.execute('SELECT `date`,variety_en,price FROM zero_spot_price;')
        records = cursor.fetchall()
        df = pd.DataFrame(records)
        return df


def read_crb():
    df = pd.read_excel('CRB指数(日).xls', skiprows=2)
    df.columns = ['date', 'crb']
    df['date'] = df['date'].apply(lambda x: x.strftime('%Y-%m-%d'))
    return df


def ruida_index(weights, suffix):  # 瑞达商品指数A
    # 能源类：原油SC（23%）、燃料油FU（5%）、低硫燃料油LU（5%）、液化气PG（6%）
    # 农产品：豆一A（6%）、生猪LH（6%）、玉米C（6%）、棉花CF（5%）、糖SR（5%）、棕榈油P（5%）、
    # 橡胶RU（5%）、豆粕M（1%）、菜粕RM（1%）、苹果AP（1%）；
    # 金属类：黄金AU（6%）、铜CU（6%）、铝AL（6%）、白银AG（1%）、镍NI（1%）

    df = read_db()
    df['dominant_price'] = df['dominant_price'].astype(float)
    df['date'] = df['date'].apply(lambda x: datetime.datetime.fromtimestamp(int(x)).strftime('%Y-%m-%d'))

    # spot = read_spot_price()
    # spot['price'] = spot['price'].astype(float)
    # spot['date'] = spot['date'].apply(lambda x: datetime.datetime.fromtimestamp(int(x)).strftime('%Y-%m-%d'))
    #
    # print(spot[spot['variety_en'] == 'LU'])

    df['weight'] = df['variety_en'].apply(lambda x: weights.get(x, None))
    # 删掉weight是nan的行
    df = df.dropna(subset=['weight'])

    print(df[df['dominant_price'] == 0.0])

    # print(df)
    # 以日期和品种分组 取第一个
    v_df = df.groupby(by=['variety_en'], as_index=False)
    ret_df = pd.DataFrame(columns=['date', 'variety_en', 'dominant_price', 'weight'])
    for group_v in v_df.groups:
        # print(group_v)
        v_df = df[df['variety_en'] == group_v].copy()
        v_df.sort_values(by=['date'], inplace=True)
        # 计算w * I(t) / I(t-1)
        v_df['value'] = v_df['weight'] / 100 * (v_df['dominant_price'] / v_df['dominant_price'].shift(1))
        # 以下up的计算结果与value相等
        # v_df['up'] = v_df['weight'] / 100 * (1 + (v_df['dominant_price'] - v_df['dominant_price'].shift(1)) / v_df['dominant_price'].shift(1))
        # v_df.dropna(inplace=True)
        # print(v_df)
        #
        # print('---' * 30)
        ret_df = pd.concat([ret_df, v_df])
    ret_df.sort_values(by=['date'], inplace=True)
    print(ret_df)
    print(ret_df[ret_df['date'] == '2021-06-10'])
    print(ret_df[ret_df['date'] == '2021-06-10']['value'].sum())
    print(ret_df[ret_df['date'] == '2021-06-10']['weight'].sum())

    date_df = ret_df.groupby(by=['date'], as_index=False).agg({'weight': 'sum', 'value': 'sum'})

    date_df['buchong'] = 100 - date_df['weight']
    date_df['real_value'] = date_df['buchong'] / 100 + date_df['value']
    date_df.iat[0, 4] = 100

    date_df['result'] = date_df['real_value'].cumprod()

    crb = read_crb()
    date_df = pd.merge(date_df, crb, on=['date'])
    print(date_df)

    date_df[['date', 'result', 'crb']].to_excel(f'result_{suffix}.xlsx')

    # for group in ret_df.groupby(by=['date'], as_index=False).groups:
    #     d_df = ret_df[ret_df['date'] == group].copy()
    #
    #     if len(weights) != d_df.shape[0]:
    #         # print(group, d_df.shape, len(weights))
    #         v_list = d_df['variety_en'].values.tolist()
    #         for v in weights.keys():
    #             if v not in v_list:
    #                 print(group, v)


if __name__ == '__main__':
    weightsA = {
        'SC': 23, 'FU': 5, 'LU': 5, 'PG': 6, 'A': 6, 'LH': 6, 'C': 6, 'CF': 5, 'SR': 5,
        'P': 5, 'RU': 5, 'M': 1, 'RM': 1, 'AP': 1, 'AU': 6, 'CU': 6, 'AL': 6, 'AG': 1, 'NI': 1
    }

    # 农产品：豆一A（6 %）、玉米C（6 %）、生猪LH（6 %）、棉花CF（5 %）、糖SR（5 %）、棕榈油P（5 %）、
    # 橡胶RU（5 %）、豆粕M（3 %）、菜粕RM（2 %）、苹果AP（2 %）；
    # 能源类：原油SC（10 %）、沥青BU（5 %）、燃料油FU（5 %）、低硫燃料油LU（5 %）、液化气PG（6 %）；
    # 金属类：黄金AU（6 %）、铜CU（6 %）、铝AL（6 %）、白银AG（3 %）、镍NI（3 %）。

    weightsB = {
        'SC': 10, 'FU': 5, 'BU': 5, 'LU': 5, 'PG': 6, 'A': 6, 'LH': 6, 'C': 6, 'CF': 5, 'SR': 5,
        'P': 5, 'RU': 5, 'M': 3, 'RM': 2, 'AP': 2, 'AU': 6, 'CU': 6, 'AL': 6, 'AG': 3, 'NI': 3
    }
    # 农产品：豆粕M（6 %）、玉米C（5 %）、棕榈油P（5 %）、橡胶RU（5 %）、棉花CF（4 %）、糖SR（4 %）、
    # 豆一A（2 %）、生猪LH（2 %）、苹果AP（2 %）；
    # 能源类：原油SC（6 %）、沥青BU（4 %）、燃料油FU（2 %）；
    # 化工类：PTA（4 %）、PP（4 %）、甲醇MA（2 %）；
    # 金属类：黄金AU（6 %）、铜CU（6 %）、白银AG（5 %）、镍NI（5 %）、铝AL（4 %）；
    # 黑色链：螺纹钢RB（6 %）、铁矿石I（5 %）、焦炭J（4 %）、焦煤JM（2 %）。

    weightsC = {
        'M': 6, 'C': 5, 'P': 5, 'RU': 5, 'CF': 4, 'SR': 4, 'A': 2, 'LH': 2, 'AP': 2,
        'SC': 6, 'BU': 4, 'FU': 2, 'TA': 4, 'PP':4, 'MA': 2, 'AU': 6, 'CU': 6, 'AG': 5,
        'NI': 5, 'AL': 4, 'RB': 6, 'I': 5, 'J': 4, 'JM': 2
    }
    # r = 0
    # for k, v in weightsC.items():
    #     r += v
    # print(r)
    ruida_index(weightsC, 'C')

