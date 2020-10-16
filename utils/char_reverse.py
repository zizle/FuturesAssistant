# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-13
# ------------------------

def strQ2B(ustring):
    """ 全角转半角 """
    rstring = ""
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code == 12288:  # 全角空格直接转换
            inside_code = 32
        elif 65281 <= inside_code <= 65374:  # 全角字符（除空格）根据关系转化
            inside_code -= 65248
        else:
            pass
        rstring += chr(inside_code)
    return rstring


def strB2Q(ustring):
    """半角转全角"""
    rstring = ""
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code == 32:  # 半角空格直接转化
            inside_code = 12288
        elif 32 <= inside_code <= 126:  # 半角字符（除空格）根据关系转化
            inside_code += 65248

        rstring += chr(inside_code)
    return rstring


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


