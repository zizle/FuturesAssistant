# _*_ coding:utf-8 _*_
# @File  : hanlder_czce_error.py
# @Time  : 2020-12-08 10:20
# @Author: zizle
import time
import datetime
import math
from db.mysql_z import ExchangeLibDB
from utils.char_reverse import split_number_en
from configs import logger

""" 处理郑商所合约错误的问题 """


def get_ten_multiple(num: int):
    """ 获取大于num最近的整十数 """
    while num % 10 != 0:
        num += 1
    return num


def handler_daily(start_id, end_id):
    with ExchangeLibDB() as ex_cursor:
        ex_cursor.execute(
            "SELECT * FROM czce_daily WHERE id>=%s AND id<=%s;", (start_id, end_id)
        )
        daily_all = ex_cursor.fetchall()
        # print(daily_all)
        if not daily_all:
            print("没有数据了")
            return False
        # 处理更新数据
        print(len(daily_all))
        for item in daily_all:
            # 取date的年份后两位与contract的年份位做比较
            item_date_str = datetime.datetime.fromtimestamp(item['date']).strftime('%Y%m%d')
            suffix_year = item_date_str[2:4]
            split_contract = split_number_en(item['contract'])
            middle_contract = split_contract[1][:2]
            # 如果contract取的数小于date取得的数，那么contract的年份位需为date的年份位+1
            if int(middle_contract) < int(suffix_year):
                # 取到最近的且大于自身的一个整10的数
                contract_year = '%02d' % get_ten_multiple(int(suffix_year))
                real_contract = split_contract[0] + '{}{}'.format(contract_year[0], middle_contract[1]) + split_contract[1][-2:]
                # print('{}数据不正常{} -> {}'.format(item_date_str, item['contract'], real_contract))
                # 更新数据
                cp = ex_cursor.execute(
                    'UPDATE czce_daily SET contract=%s WHERE id=%s;', (real_contract, item['id'])
                )
                print('{}-{}数据不正常,由{}->{},更新影响了记录数:{}'.format(item['id'], item['date'], item['contract'], real_contract,cp))
                logger.error('{}-{}数据不正常,由{}->{},更新影响了记录数:{}'.format(item['id'], item['date'], item['contract'], real_contract, cp))
        return True


def handler_rank(start_id, end_id):
    with ExchangeLibDB() as ex_cursor:
        ex_cursor.execute(
            "SELECT * FROM czce_rank WHERE id>=%s AND id<=%s;", (start_id, end_id)
        )
        rank_all = ex_cursor.fetchall()
        # print(daily_all)
        if not rank_all:
            print("没有数据了")
            return False
        # 处理更新数据
        print(len(rank_all))
        for item in rank_all:
            if item['contract'] == item['variety_en']:  # 相同的则是品种的排名,跳过
                continue
            # print(item)
            # 取date的年份后两位与contract的年份位做比较
            item_date_str = datetime.datetime.fromtimestamp(item['date']).strftime('%Y%m%d')
            suffix_year = item_date_str[2:4]
            split_contract = split_number_en(item['contract'])
            middle_contract = split_contract[1][:2]
            # 如果contract取的数小于date取得的数，那么contract的年份位需为date最近的整十年份
            if int(middle_contract) < int(suffix_year):
                contract_year = '%02d' % get_ten_multiple(int(suffix_year))
                real_contract = split_contract[0] + '{}{}'.format(contract_year[0], middle_contract[1]) + split_contract[1][-2:]
                # 更新数据
                cp = ex_cursor.execute(
                    'UPDATE czce_rank SET contract=%s WHERE id=%s;', (real_contract, item['id'])
                )
                print('{}-{}数据不正常,由{}->{},更新影响了记录数:{}'.format(item['id'], item['date'], item['contract'],
                                                              real_contract, cp))
                logger.error('{}-{}数据不正常,由{}->{},更新影响了记录数:{}'.format(item['id'], item['date'], item['contract'],
                                                                     real_contract, cp))
        return True


if __name__ == '__main__':
    flag = True
    count = 0
    while flag:
        s = count * 10000
        e = s + 9999
        # flag = handler_daily(s, e)
        flag = handler_rank(s, e)
        count += 1
        time.sleep(1)

