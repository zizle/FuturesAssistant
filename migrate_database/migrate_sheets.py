# _*_ coding:utf-8 _*_
# @File  : migrate_sheets.py
# @Time  : 2020-09-16 14:57
# @Author: zizle
""" 迁移品种数据组和数据表 """
import time
import pandas as pd
import numpy as np
from datetime import datetime
from old_database import OldSqlZ
from db.mysql_z import MySqlZ, VarietySheetDB

pd.set_option('mode.chained_assignment', None)  # pandas不提示警告


def migrate_sheet_group():
    with OldSqlZ() as cursor:
        cursor.execute(
            "SELECT varietytb.name_en,grouptb.name,grouptb.author_id "
            "FROM info_variety_trendgroup AS grouptb "
            "INNER JOIN info_variety AS varietytb "
            "ON grouptb.variety_id=varietytb.id;"
        )
        groups = cursor.fetchall()

    to_saves = list()
    for group_item in groups:

        if group_item["author_id"] == 19:
            continue
        if group_item["name_en"] == "PTA":
            group_item["name_en"] = "TA"
        if group_item["name_en"] == "GZ":
            group_item["name_en"] = "GP"
        if group_item["name_en"] == "GZQH":
            group_item["name_en"] = "GZ"
        if group_item["name_en"] == "HGJJ":
            group_item["name_en"] = "HG"
        if group_item["name_en"] == "GZWH":
            group_item["name_en"] = "WH"

        item = {
            "variety_en": group_item["name_en"],
            "group_name": group_item["name"]
        }
        to_saves.append(item)

    with MySqlZ() as cursor:
        cursor.executemany(
            "INSERT INTO industry_sheet_group (variety_en,group_name) VALUES "
            "(%(variety_en)s,%(group_name)s);",
            to_saves
        )


def migrate_sheets():
    """ 迁移数据表 """
    # 查询新的所有数据分组
    with MySqlZ() as mycursor:
        mycursor.execute(
            "SELECT * FROM industry_sheet_group;"
        )
        group_all = mycursor.fetchall()
        # 查询所有用户
        mycursor.execute("SELECT * FROM user_user;")
        all_users = mycursor.fetchall()
    group_dict = {group_item["variety_en"] + "_" + group_item["group_name"]: group_item["id"] for group_item in
                  group_all}
    users_dict = {user_item["phone"]: user_item["id"] for user_item in all_users}

    with OldSqlZ() as cursor:
        cursor.execute(
            "SELECT trendtb.create_time,trendtb.update_time,trendtb.title,trendtb.title_md5,"
            "trendtb.suffix_index,trendtb.sql_table,trendtb.group_id,trendtb.variety_id,trendtb.author_id,"
            "trendtb.min_date,trendtb.max_date,trendtb.is_active,trendtb.new_count,trendtb.note,"
            "grouptb.name,usertb.phone "
            "FROM info_trend_table AS trendtb "
            "INNER JOIN info_variety_trendgroup AS grouptb "
            "ON trendtb.group_id=grouptb.id "
            "INNER JOIN info_user AS usertb "
            "ON trendtb.author_id=usertb.id;"
        )
        all_tables = cursor.fetchall()

        count = len(all_tables)

        for index, table_item in enumerate(all_tables):
            print(index + 1, count)
            if table_item["author_id"] == 19:
                continue
            table_name_list = table_item["sql_table"].split("_")
            if table_name_list[0] == "MYZS":
                continue

            if table_name_list[0] == "PTA":
                table_name_list[0] = "TA"
            if table_name_list[0] == "GZ":
                table_name_list[0] = "GP"
            if table_name_list[0] == "GZQH":
                table_name_list[0] = "GZ"
            if table_name_list[0] == "HGJJ":
                table_name_list[0] = "HG"
            if table_name_list[0] == "GZWH":
                table_name_list[0] = "WH"
            table_name_list[1] = "SHEET"

            new_group_id = group_dict.get(table_name_list[0] + "_" + table_item["name"], None)
            if new_group_id is None:
                continue
            new_user_id = users_dict.get(table_item["phone"])
            # print("原数据表名称:", table_item["sql_table"])
            # print("新数据表名称:", '_'.join(table_name_list))
            # print("原数据表分组:", table_item['group_id'])
            # print("新数据表分组:", new_group_id)
            # print("原数据表用户id:", table_item['author_id'])
            # print("新数据表用户id:", new_user_id)

            # # 修改表名称
            # cursor.execute("ALTER TABLE %s RENAME TO %s;" % (table_item["sql_table"], '_'.join(table_name_list)))
            # 迁移表到新表中
            # 查询数据表的源数据
            cursor.execute("SELECT * FROM %s;" % table_item["sql_table"])
            table_values = cursor.fetchall()
            sheet_message = save_sheet_to_sheet_db(table_values, table_name_list[0], table_item["suffix_index"])
            table_name_list[2] = str(table_item["suffix_index"])
            if sheet_message:
                # 整理新的数据结构
                new_item = {
                    "create_time": table_item["create_time"],
                    "creator": new_user_id,
                    "update_time": table_item["update_time"],
                    "update_by": new_user_id,
                    "variety_en": table_name_list[0],
                    "group_id": new_group_id,
                    "sheet_name": table_item["title"],
                    "name_md5": table_item["title_md5"],
                    "db_table": '_'.join(table_name_list),
                    "min_date": sheet_message["min_date"],
                    "max_date": sheet_message["max_date"],
                    "update_count": table_item["new_count"],
                    "suffix": table_item["suffix_index"]
                }
                # 创建数据表的记录表
                # with MySqlZ() as cursor:
                #     cursor.execute(
                #         "INSERT INTO industry_user_sheet (creator,update_by,variety_en,group_id,sheet_name,name_md5,"
                #         "db_table,min_date,max_date,update_count,suffix) "
                #         "VALUES (%(creator)s,%(update_by)s,%(variety_en)s,%(group_id)s,%(sheet_name)s,%(name_md5)s,"
                #         "%(db_table)s,%(min_date)s,%(max_date)s,%(update_count)s,%(suffix)s);",
                #         sheet_message
                #     )
                with MySqlZ() as mycursor:
                    mycursor.execute(
                        "INSERT INTO industry_user_sheet (create_time,creator,update_time,update_by,variety_en,group_id,"
                        "sheet_name,name_md5,db_table,min_date,max_date,update_count,suffix) "
                        "VALUES (%(create_time)s,%(creator)s,%(update_time)s,%(update_by)s,%(variety_en)s,%(group_id)s,"
                        "%(sheet_name)s,%(name_md5)s,%(db_table)s,%(min_date)s,%(max_date)s,%(update_count)s,%(suffix)s);",
                        new_item
                    )
                print("保存品种表{}:{}完成".format(table_name_list[0], table_item["title"]))
                time.sleep(0.3)


def verify_date_time(date_time):
    try:
        datetime.strptime(date_time, "%Y-%m-%d")
    except Exception:
        return np.nan
    return date_time


def save_sheet_to_sheet_db(table_values, variety_en, sheet_suffix_index):
    """ 保存数据表的源数据到数据库中 """
    values_df = pd.DataFrame(table_values)
    # 删除create_time和update_time
    del values_df["create_time"]
    del values_df["update_time"]
    del values_df["id"]
    values_df.iloc[1:]["column_0"] = values_df.iloc[1:]["column_0"].apply(verify_date_time)

    values_df.iloc[:1].fillna('', inplace=True)  # 替换第一行中有的nan
    values_df.iloc[:, 1:values_df.shape[1]].fillna('', inplace=True)  # 替换除第一列以外的nan为空
    values_df.dropna(axis=0, how='any', inplace=True)  # 删除含nan的行
    if values_df.empty:
        print("数据表为空")
        return {}
    # 取出表头
    last_index = len(values_df.columns) - 1
    col_name = ""
    field_name = "id INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
    val_name = ""
    for index, col_item in enumerate(values_df.columns.values.tolist()):
        if index == last_index:
            col_name += col_item
            val_name += "%(" + col_item + ")s"
            field_name += "column_{} VARCHAR(80) DEFAULT ''".format(index)
        else:
            col_name += col_item + ","
            val_name += "%(" + col_item + ")s" + ","
            field_name += "column_{} VARCHAR(80) DEFAULT ''".format(index) + ","

    table_name = "{}_SHEET_{}".format(variety_en, sheet_suffix_index)
    create_statement = "CREATE TABLE %s (%s) DEFAULT CHARSET='utf8';" % (table_name, field_name)
    insert_statement = "INSERT INTO %s (%s) VALUES (%s);" % (table_name, col_name, val_name)
    new_values = values_df.to_dict(orient="records")
    # 保存表
    with VarietySheetDB() as cursor:
        cursor.execute(create_statement)  # 创建数据表
        update_count = cursor.executemany(insert_statement, new_values)
        # 查询表的最大值和最小值
        cursor.execute("SELECT MIN(column_0) AS min_date,MAX(column_0) AS max_date FROM %s WHERE id>2;" % table_name)
        date_msg = cursor.fetchone()
    min_date, max_date = "", ""
    if date_msg:
        if date_msg["min_date"] is not None:
            min_date = date_msg["min_date"]
        if date_msg["max_date"] is not None:
            max_date = date_msg["max_date"]
    print("迁移表成功")
    return {
        "update_count": update_count,
        "min_date": min_date,
        "max_date": max_date,
        "db_table": table_name,
        "suffix": sheet_suffix_index
    }


if __name__ == '__main__':
    # migrate_sheet_group()  # 迁移品种数据组
    migrate_sheets()
