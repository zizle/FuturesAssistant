# _*_ coding:utf-8 _*_
# @File  : compare_util.py
# @Time  : 2021-05-21 09:00
# @Author: zizle

# 对比解读
import re
import datetime

def float_string(x: str):
    try:
        return round(float(x), 4)
    except Exception:
        return 0


def week_compare(df, head_name):
    # header_name括号你的文字 => 单位
    result_list = re.findall(r"[(](.*?)[)]", head_name)
    unit_text = result_list[0] if result_list else ''
    if unit_text:
        head_name = head_name.replace(f'({unit_text})', '')
    df.columns = ['date', 'value']
    df['year_week'] = df['date'].apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').strftime('%Y%W'))
    # 排序
    df.sort_values(by=['date'], inplace=True)
    # 按周,按月,按年去取得3个数据框进行运算
    week_df = df.groupby(by=['year_week']).last().reset_index()  # 按周取数取最后一条数据
    week_df['value'] = week_df['value'].apply(float_string)
    last_week, this_week = week_df.tail(2).to_dict(orient='records')
    # print('最新周数据:', this_week)
    # print('上周数据:', last_week)
    updown = round(this_week['value'] - last_week['value'], 2)
    up_percent = round(updown * 100 / last_week['value'], 4) if last_week['value'] != 0 else 100
    up_text = ['增加', '增幅']
    if updown < 0:
        updown = -updown
        up_percent = -up_percent
        up_text = ['减少', '减幅']
    # 组织数据
    text = f'本周{this_week["date"]},{head_name}:{this_week["value"]}{unit_text},' \
           f'较上周{last_week["date"]},{head_name}:{last_week["value"]}{unit_text},{up_text[0]}{updown}{unit_text},{up_text[1]}{up_percent}%.'
    del df
    return text


def month_compare(df, head_name):
    result_list = re.findall(r"[(](.*?)[)]", head_name)
    unit_text = result_list[0] if result_list else ''
    if unit_text:
        head_name = head_name.replace(f'({unit_text})', '')
    df.columns = ['date', 'value']
    df['year_month'] = df['date'].apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').strftime('%Y%m'))
    # 排序
    df.sort_values(by=['date'], inplace=True)
    month_df = df.groupby(by=['year_month']).last().reset_index()  # 按月取数取最后一条数据
    # print(month_df)
    month_df['value'] = month_df['value'].apply(float_string)
    last_month, this_month = month_df.tail(2).to_dict(orient='records')
    updown = round(this_month['value'] - last_month['value'], 2)
    up_percent = round(updown * 100 / last_month['value'], 4) if last_month != 0 else 100
    up_text = ['增加', '增幅']
    if updown < 0:
        updown = -updown
        up_percent = -up_percent
        up_text = ['减少', '减幅']
    # 组织数据
    text = f'本月{this_month["date"]},{head_name}:{this_month["value"]}{unit_text},' \
           f'较上月{last_month["date"]},{head_name}:{last_month["value"]}{unit_text},{up_text[0]}{updown}{unit_text},{up_text[1]}{up_percent}%.'
    del df
    return text


def year_compare(df, head_name):
    result_list = re.findall(r"[(](.*?)[)]", head_name)
    unit_text = result_list[0] if result_list else ''
    if unit_text:
        head_name = head_name.replace(f'({unit_text})', '')
    df.columns = ['date', 'value']
    df['value'] = df['value'].apply(float_string)
    # 排序
    df.sort_values(by=['date'], inplace=True)
    df['year'] = df['date'].apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').strftime('%Y%m%d')).astype(int)

    cur_day = df.tail(1).to_dict(orient='records')[0]

    diff_year = cur_day['year'] - 10000
    year_start = (cur_day['year'] // 10000 - 1) * 10000 + 101
    year_end = (cur_day['year'] // 10000 - 1) * 10000 + 1231

    year_df = df[(df['year'] >= year_start) & (df['year'] <= year_end)].copy()
    year_df['year_diff'] = year_df['year'] - diff_year
    # 取year_diff最小的行
    year_df = year_df[year_df['year_diff'] >= 0]
    year_df = year_df[year_df['year_diff'] == year_df['year_diff'].min()]  # 得到去年同期最近的值
    last_year = year_df.to_dict(orient='record')[0]
    # print('当前日期', cur_day)
    # print('去年同期', last_year)
    updown = round(cur_day['value'] - last_year['value'], 2)
    up_percent = round(updown * 100 / last_year['value'], 4) if last_year['value'] != 0 else 100
    up_text = ['增加', '增幅']
    if updown < 0:
        updown = -updown
        up_percent = -up_percent
        up_text = ['减少', '减幅']
    # 组织数据
    text = f'当前{cur_day["date"]},{head_name}:{cur_day["value"]}{unit_text},' \
           f'较去年同期{last_year["date"]},{head_name}:{last_year["value"]}{unit_text},{up_text[0]}{updown}{unit_text},{up_text[1]}{up_percent}%.'
    del df
    return text

