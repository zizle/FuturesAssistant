# _*_ coding:utf-8 _*_
# @File  : hanlder_czce_error.py
# @Time  : 2020-12-08 10:20
# @Author: zizle
import time
import math
from db.mysql_z import ExchangeLibDB
from utils.char_reverse import split_number_en
from configs import logger

""" 处理郑商所合约错误的问题 """


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
            suffix_year = item['date'][2:4]
            split_contract = split_number_en(item['contract'])
            middle_contract = split_contract[1][:2]
            # 如果contract取的数小于date取得的数，那么contract的年份位需为date的年份位+1
            if int(suffix_year) > int(middle_contract):
                real_year = '%02d' % (int(suffix_year) + 1)
                real_contract = split_contract[0] + real_year + split_contract[1][-2:]
                # 更新数据
                cp = ex_cursor.execute(
                    'UPDATE czce_daily SET contract=%s WHERE id=%s;', (real_contract, item['id'])
                )
                print('{}-{}数据不正常,更新影响了记录数:{}'.format(item['id'], item['date'], cp))
                logger.error('{}-{}数据不正常,更新影响了记录数:{}'.format(item['id'], item['date'], cp))
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
            suffix_year = item['date'][2:4]
            split_contract = split_number_en(item['contract'])
            middle_contract = split_contract[1][:2]
            # 如果contract取的数小于date取得的数，那么contract的年份位需为date的年份位+1
            if int(suffix_year) > int(middle_contract):
                real_year = '%02d' % (int(suffix_year) + 1)
                real_contract = split_contract[0] + real_year + split_contract[1][-2:]
                # 更新数据
                cp = ex_cursor.execute(
                    'UPDATE czce_rank SET contract=%s WHERE id=%s;', (real_contract, item['id'])
                )
                print('{}-{}数据不正常,更新影响了记录数:{}'.format(item['id'], item['date'], cp))
                logger.error('{}-{}数据不正常,更新影响了记录数:{}'.format(item['id'], item['date'], cp))
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
        time.sleep(2)

