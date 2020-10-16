# _*_ coding:utf-8 _*_
# @File  : migrate_charts.py
# @Time  : 2020-09-17 08:07
# @Author: zizle
""" 迁移数据图形 """
import json
import os
import time
from old_database import OldSqlZ
from db.mysql_z import MySqlZ


def query_new_user_and_sheet(phone, name_md5):
    with MySqlZ() as mycursor:
        mycursor.execute("SELECT id FROM user_user WHERE phone=%s;", (phone, ))
        user_info = mycursor.fetchone()

        mycursor.execute("SELECT id FROM industry_user_sheet WHERE name_md5=%s;", (name_md5, ))
        sheet_info = mycursor.fetchone()
    if not user_info or not sheet_info:
        return None, None
    return user_info["id"], sheet_info["id"]


with OldSqlZ() as cursor:
    cursor.execute(
        "SELECT charttb.id,charttb.create_time,charttb.title,charttb.options_file,charttb.decipherment,"
        "charttb.is_trend_show,charttb.is_variety_show,charttb.suffix_index,"
        "usertb.phone,sheettb.title_md5,varietytb.name_en "
        "FROM info_trend_echart AS charttb "
        "INNER JOIN info_trend_table AS sheettb "
        "ON charttb.table_id=sheettb.id "
        "INNER JOIN info_user AS usertb "
        "ON charttb.author_id=usertb.id "
        "INNER JOIN info_variety AS varietytb "
        "ON charttb.variety_id=varietytb.id; "
    )

    charts = cursor.fetchall()

for chart_item in charts:
    if chart_item["name_en"] == "PTA":
        chart_item["name_en"] = "TA"
    if chart_item["name_en"] == "GZ":
        chart_item["name_en"] = "GP"
    if chart_item["name_en"] == "GZQH":
        chart_item["name_en"] = "GZ"
    if chart_item["name_en"] == "HGJJ":
        chart_item["name_en"] = "HG"
    if chart_item["name_en"] == "GZWH":
        chart_item["name_en"] = "WH"
    print(chart_item)
    # 查询新数据库中的用户ID和数据表id
    user_id, sheet_id = query_new_user_and_sheet(chart_item["phone"], chart_item["title_md5"])
    if not user_id or not sheet_id:
        continue
    # 替换新的配置文件名称
    opt_file_path = "ChartOption/{}/{}".format(user_id, chart_item["options_file"][-45:])
    # 读取配置文件内容,整理保存
    old_opt_file = os.path.join("E:/", chart_item["options_file"])
    with open(old_opt_file) as fp:
        chart_option_json = json.load(fp)

    # 配置新文件格式
    title_opt = chart_option_json["title"]
    x_axis_opt = chart_option_json["x_axis"][0]
    start_year = x_axis_opt["start"] if x_axis_opt["start"] else "0"
    end_year = x_axis_opt["end"] if x_axis_opt["end"] else "0"
    date_len_dict = {
        "%Y-%m-%d": 10,
        "%Y-%m": 7,
        "%Y": 4
    }
    # 左轴参数
    y_axis = [
        {"type": "value", "name": chart_option_json["axis_tags"]["left"]}
    ]
    if chart_option_json["y_left_min"]:
        y_axis[0]["min"] = float(chart_option_json["y_left_min"])
    if chart_option_json["y_left_max"]:
        y_axis[0]["max"] = float(chart_option_json["y_left_max"])
    if chart_option_json["y_right"]:
        right_item = {
            "type": "value", "name": chart_option_json["axis_tags"]["right"]
        }
        if chart_option_json["y_right_min"]:
            right_item["min"] = float(chart_option_json["y_right_min"])
        if chart_option_json["y_right_max"]:
            right_item["max"] = float(chart_option_json["y_right_max"])
        y_axis.append(right_item)

    # 生成series_data
    series_data = list()
    for left_item in chart_option_json["y_left"]:
        contain_zero = 0 if left_item["no_zero"] in [1, 2] else 1
        item = {
            "axis_index": 0,
            "chart_type": left_item["chart_type"],
            "column_index": left_item["col_index"],
            "contain_zero": contain_zero
        }
        series_data.append(item)

    for right_item in chart_option_json["y_right"]:
        contain_zero = 0 if right_item["no_zero"] in [1, 2] else 1
        item = {
            "axis_index": 1,
            "chart_type": right_item["chart_type"],
            "column_index": right_item["col_index"],
            "contain_zero": contain_zero
        }
        series_data.append(item)
    # 水印
    watermark = chart_option_json["watermark_text"] if chart_option_json["watermark"] else ""
    # 类型

    chart_category = "normal" if chart_option_json["typec"] == "single" else "season"
    # 右轴参数
    new_json = {
        "title": {
            "text": title_opt["text"],
            "font_size": title_opt["textStyle"]["fontSize"],
        },
        "x_axis": {
            "column_index": x_axis_opt["col_index"],
            "date_length": date_len_dict.get(x_axis_opt["date_format"], 10)
        },
        "y_axis": y_axis,
        "series_data": series_data,
        "watermark": watermark,
        "start_year": start_year,
        "end_year": end_year,
        "chart_category": chart_category
    }
    # 将新配置保存到新文件中
    new_path = os.path.join("F:/", opt_file_path)
    # 创建文件夹
    new_folder, _ = os.path.split(new_path)
    if not os.path.exists(new_folder):
        os.makedirs(new_folder)
    with open(new_path, 'w', encoding="utf-8") as fp:
        json.dump(new_json, fp, indent=4)
    time.sleep(0.01)
    print("保存新配置文件成功")
    # 在新的数据库保存新的图形名称
    new_option_record = {
        "create_time": chart_item["create_time"],
        "creator": user_id,
        "title": chart_item["title"],
        "variety_en": chart_item["name_en"],
        "sheet_id": sheet_id,
        "option_file": opt_file_path,
        "decipherment": chart_item["decipherment"],
        "suffix": chart_item["suffix_index"],
        "is_principal": "2" if chart_item["is_trend_show"] else "0",
        "is_petit": chart_item["is_variety_show"]
    }
    with MySqlZ() as mycursor:
        mycursor.execute(
            "INSERT INTO industry_user_chart ("
            "create_time,creator,title,variety_en,sheet_id,option_file,decipherment,suffix,is_principal,is_petit) "
            "VALUES (%(create_time)s,%(creator)s,%(title)s,%(variety_en)s,%(sheet_id)s,%(option_file)s,%(decipherment)s,"
            "%(suffix)s,%(is_principal)s,%(is_petit)s);",
            new_option_record
        )
    print("保存图形表记录成功")
    time.sleep(0.5)
