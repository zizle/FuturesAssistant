# _*_ coding:utf-8 _*_
# @File  : utils.py
# @Time  : 2021-04-14 10:54
# @Author: zizle
import random
import time
from hashlib import md5
from itertools import groupby


def create_random_string(count: int = 6):
    s = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join([s[random.randint(0, 61)] for _ in range(count)])


def generate_random_filename():
    hash_handler = md5(str(time.time()).encode("utf-8"))
    return hash_handler.hexdigest()


def split_number_en(ustring):
    return [''.join(list(g)) for k, g in groupby(ustring, key=lambda x: x.isdigit())]


def full_width_to_half_width(ustring):
    """ 全角转半角 """
    reverse_str = ""
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code == 12288:  # 全角空格直接转换
            inside_code = 32
        elif 65281 <= inside_code <= 65374:  # 全角字符（除空格）根据关系转化
            inside_code -= 65248
        else:
            pass
        reverse_str += chr(inside_code)
    return reverse_str


def half_width_to_full_width(ustring):
    """半角转全角"""
    reverse_str = ""
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code == 32:  # 半角空格直接转化
            inside_code = 12288
        elif 32 <= inside_code <= 126:  # 半角字符（除空格）根据关系转化
            inside_code += 65248
        reverse_str += chr(inside_code)
    return reverse_str


def split_zh_en(ustring):
    """分离中英文"""
    zh_str = ""
    en_str = ""
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code <= 256:
            en_str += uchar
        else:
            zh_str += uchar
    if not zh_str:
        zh_str = en_str
    return zh_str.strip(), en_str.strip()


def get_ten_multiple(num: int):
    """ 获取大于num最近的整十数 """
    while num % 10 != 0:
        num += 1
    return num


# 将品种月份修改为品种+4位合约的形式
def modify_contract_express(contract, date_str):
    split_contract = split_number_en(contract)
    contract = date_str[2].join(split_contract)  # 可能不是正确的合约年,需继续处理
    split_contract = split_number_en(contract)
    middle_contract = split_contract[1][:2]
    suffix_year = date_str[2:4]
    if int(middle_contract) < int(suffix_year):
        contract_year = '%02d' % get_ten_multiple(int(suffix_year))
        real_contract = split_contract[0] + '{}{}'.format(contract_year[0], middle_contract[1]) + split_contract[1][-2:]
        return real_contract
    return contract


def list2tree(data: list, pid: int):
    return [dict(menu, **{'children': list2tree(data, menu['id'])}) for menu in
            [m for m in data if m['parent_id'] == pid]]
