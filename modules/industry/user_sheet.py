# _*_ coding:utf-8 _*_
# @File  : user_sheet.py
# @Time  : 2020-09-03 15:58
# @Author: zizle

""" 用户的数据表
API-1: 创建品种树表的组别
API-2: 获取指定品种的数据表组别
API-3: 用户上传品种数据表(新建与更新)
API-4: 获取指定品种下的数据表名称信息列表
API-5: 指定数据表的具体表内数据
API-6: 交换指定两个表的显示排序
API-7: 用户删除自己创建的数据表
API-8: 用户修改自己的数据表是否公开
API-9: 用户指定修改某个数据表下的某条数据记录
"""
import re
import os
import numpy as np
import pandas as pd
from datetime import datetime
from hashlib import md5
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from utils.verify import oauth2_scheme, decipher_user_token
from db.mysql_z import MySqlZ, VarietySheetDB
from configs import FILE_STORAGE, logger
from .models import SheetData, SwapSuffixItem

sheet_router = APIRouter()

pd.set_option('mode.chained_assignment', None)      # pandas不提示警告


# 验证品种
def verify_variety(variety_en: str):
    if not re.match(r'^[A-Z]{1,2}$', variety_en):
        raise HTTPException(detail="Invalidate Variety!", status_code=400)
    return variety_en


# 验证时间类型
def verify_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except Exception as e:
        return np.nan
    return date_str


# 用户有权限的品种自己创建数据分组
@sheet_router.post("/variety/{variety_en}/sheet-group/", summary="用户为品种创建数据表分组")
async def create_sheet_group(
        variety_en: str = Depends(verify_variety),
        user_token: str = Depends(oauth2_scheme),
        group_name: str = Body(..., embed = True)
):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="登录信息失效了")
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,variety_en FROM basic_variety WHERE variety_en=%s;", (variety_en, )
        )
        variety_info = cursor.fetchone()
        if not variety_info:
            raise HTTPException(status_code=403, detail="不能为不存在的品种添加分组")
        cursor.execute(
            "INSERT INTO industry_sheet_group (variety_en, group_name) VALUES (%s,%s);",
            (variety_info["variety_en"], group_name)
        )
        cursor.execute(
            "SELECT id,variety_en,group_name FROM industry_sheet_group "
            "WHERE variety_en=%s AND is_active=1 ORDER BY suffix DESC;",
            (variety_info["variety_en"],)
        )
        groups = cursor.fetchall()
    return {"message": "创建数据分组成功!", "groups": groups}


@sheet_router.get("/variety/{variety_en}/sheet-group/", summary="获取品种下的数据分组")
async def variety_sheet_group(variety_en: str = Depends(verify_variety)):
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,variety_en,group_name FROM industry_sheet_group "
            "WHERE variety_en=%s AND is_active=1 ORDER BY suffix DESC;",
            (variety_en, )
        )
        groups = cursor.fetchall()
    return {"message": "获取分组成功!", "groups": groups}


""" 用户上传新表和更新表数据开始 """


def save_new_sheet(
        variety_en: str,
        sheet_headers: list,
        sheet_suffix_index: int,
        source_df: pd.DataFrame
):
    """ 保存新的数据表 """
    last_index = len(source_df.columns) - 1
    col_name = ""
    field_name = "id INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
    val_name = ""
    headers_values = dict()
    for index, col_item in enumerate(source_df.columns.values.tolist()):
        if index == last_index:
            col_name += col_item
            val_name += "%(" + col_item + ")s"
            field_name += "column_{} VARCHAR(80) DEFAULT ''".format(index)
        else:
            col_name += col_item + ","
            val_name += "%(" + col_item + ")s" + ","
            field_name += "column_{} VARCHAR(80) DEFAULT ''".format(index) + ","

        headers_values[col_item] = sheet_headers[index]

    table_name = "{}_SHEET_{}".format(variety_en, sheet_suffix_index)
    drop_table_statement = "DROP TABLE IF EXISTS %s;" % table_name
    create_statement = "CREATE TABLE %s (%s) DEFAULT CHARSET='utf8';" % (table_name, field_name)
    insert_statement = "INSERT INTO %s (%s) VALUES (%s);" % (table_name, col_name, val_name)
    new_values = source_df.to_dict(orient="records")
    # 日志记录用户创建表
    logger.info('用户新建表:\n{}'.format(create_statement))
    with VarietySheetDB() as cursor:
        cursor.execute(drop_table_statement)  # 如果之前有创建成功的表但记录出错则可删除
        cursor.execute(create_statement)  # 创建数据表
        cursor.execute(insert_statement, headers_values)  # 新增表头的数据
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

    return {
        "update_count": update_count,
        "min_date": min_date,
        "max_date": max_date,
        "db_table": table_name,
        "suffix": sheet_suffix_index
    }


def update_old_sheet(source_df: pd.DataFrame, db_table: str):
    """ 更新老数据表 """
    with VarietySheetDB() as cursor:
        # 查询表中最大的数据时间
        cursor.execute("SELECT `id`, MAX(column_0) AS max_date FROM %s WHERE id>1;" % db_table)
        exist_info = cursor.fetchone()
        # 查询这表表头,根据表头列截取数据
        cursor.execute("SELECT * FROM %s WHERE id=1;" % db_table)
        sheet_headers_dict = cursor.fetchone()
        # 根据headers生成column列(防止新增列后出现的错误)
        columns_indexes = ["column_{}".format(i) for i in range(len(sheet_headers_dict) - 1)]  # 减1为id列
        # 截取数据
        source_df = source_df.reindex(columns=columns_indexes, fill_value='')
        if exist_info:
            max_date = exist_info["max_date"]
            if max_date is not None:
                # 选取数据框中时间大于查询出的时间
                cache_df = source_df.iloc[1:]   # 切掉第一行数据(自由行,可能为中文就会最大,无法去掉)
                source_df = cache_df[max_date < cache_df['column_0']]
        else:
            # 切掉第一行数据(自由行已在创建时加入过)
            source_df = source_df.iloc[1:]

        update_count = 0
        if not source_df.empty:
            # 插入数据
            last_index = len(source_df.columns) - 1
            col_name = ""
            val_name = ""
            for index, col_item in enumerate(source_df.columns.values.tolist()):
                if index == last_index:
                    col_name += col_item
                    val_name += "%(" + col_item + ")s"
                else:
                    col_name += col_item + ","
                    val_name += "%(" + col_item + ")s" + ","
            new_values = source_df.to_dict(orient="records")
            insert_statement = "INSERT INTO %s (%s) VALUES (%s);" % (db_table, col_name, val_name)
            update_count = cursor.executemany(insert_statement, new_values)
        # 查询表的最大值和最小值
        cursor.execute("SELECT MIN(column_0) AS min_date,MAX(column_0) AS max_date FROM %s WHERE id>2;" % db_table)
        date_msg = cursor.fetchone()
    min_date, max_date = "", ""
    if date_msg:
        if date_msg["min_date"] is not None:
            min_date = date_msg["min_date"]
        if date_msg["max_date"] is not None:
            max_date = date_msg["max_date"]

    return {
        "update_count": update_count,
        "min_date": min_date,
        "max_date": max_date,
    }


def discriminate_sheet(variety_en, group_id, sheet_name_md5):
    """ 区分表是否存在数据库中 """
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT `id`,`sheet_name`,db_table FROM industry_user_sheet "
            "WHERE name_md5=%s AND variety_en=%s AND group_id=%s;", (sheet_name_md5, variety_en, group_id)
        )
        is_exist = cursor.fetchone()
        if is_exist:
            return True, is_exist["db_table"]
        else:
            # 查询品种中最大表的编号
            cursor.execute(
                "SELECT `id`, MAX(suffix) AS max_suffix FROM industry_user_sheet "
                "WHERE variety_en=%s;", (variety_en, )
            )
            suffix_index_ret = cursor.fetchone()['max_suffix']
            suffix_index = 1 if not suffix_index_ret else suffix_index_ret + 1
            return False, suffix_index


@sheet_router.post("/variety/{variety_en}/sheet/", summary="用户上传品种数据表")
async def variety_sheet(
        user_token: str = Depends(oauth2_scheme),
        variety_en: str = Depends(verify_variety),
        source_data: SheetData = Body(...)
):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token Expired!")  # 400 -> 302  401 -> 204  (PyQt5)
    body_variety_en = source_data.variety_en
    group_id = source_data.group_id
    sheet_name = source_data.sheet_name
    name_md5 = md5(sheet_name.encode("utf-8")).hexdigest()
    sheet_headers = source_data.sheet_headers
    sheet_values = source_data.sheet_values
    if body_variety_en != variety_en:
        raise HTTPException(status_code=400, detail="The Variety Illegal!")
    if not all([variety_en, group_id, sheet_name, sheet_headers, sheet_values]):  # 为空值数据验证会通过
        raise HTTPException(status_code=400, detail="Invalid Values!")

    source_df = pd.DataFrame(sheet_values)
    if len(sheet_headers) != len(source_df.columns):
        raise HTTPException(status_code=400, detail="Invalid Values!")
    source_df["column_0"] = source_df["column_0"].apply(verify_date)
    source_df.iloc[:1].fillna('', inplace=True)  # 替换第一行中有的nan
    source_df.iloc[:, 1:source_df.shape[1]].fillna('', inplace=True)  # 替换除第一列以外的nan为空
    source_df.dropna(axis=0, how='any', inplace=True)  # 删除含nan的行
    if source_df.empty:  # 处理后为空的数据继续下一个
        return {"message": "数据上传成功,没有发现数据可保存!"}
    source_df = source_df.applymap(str)  # 全转为str类型
    # 新建表保存数据或者原有表更新数据(如果存在,则db_table_or_suffix为表名称,否则为新表后缀编号)
    is_exist, db_table_or_suffix = discriminate_sheet(variety_en, group_id, name_md5)
    if is_exist:  # 更新旧表
        sheet_message = update_old_sheet(source_df, db_table_or_suffix)
        sheet_message["update_by"] = user_id
        sheet_message['variety_en'] = variety_en
        sheet_message["group_id"] = group_id
        sheet_message["name_md5"] = name_md5
        sheet_message["update_time"] = datetime.now()
        # 更新品种表的数据记录
        with MySqlZ() as cursor:
            cursor.execute(
                "UPDATE industry_user_sheet SET update_by=%(update_by)s,update_time=%(update_time)s,"
                "min_date=%(min_date)s,max_date=%(max_date)s,update_count=%(update_count)s "
                "WHERE variety_en=%(variety_en)s AND group_id=%(group_id)s AND name_md5=%(name_md5)s;",
                sheet_message
            )
    else:  # 创建新表
        sheet_message = save_new_sheet(variety_en, sheet_headers, db_table_or_suffix, source_df)
        sheet_message["creator"] = user_id
        sheet_message["update_by"] = user_id
        sheet_message['variety_en'] = variety_en
        sheet_message["group_id"] = group_id
        sheet_message["sheet_name"] = sheet_name
        sheet_message["name_md5"] = name_md5
        # 新增品种表的数据记录
        with MySqlZ() as cursor:
            cursor.execute(
                "INSERT INTO industry_user_sheet (creator,update_by,variety_en,group_id,sheet_name,name_md5,"
                "db_table,min_date,max_date,update_count,suffix) "
                "VALUES (%(creator)s,%(update_by)s,%(variety_en)s,%(group_id)s,%(sheet_name)s,%(name_md5)s,"
                "%(db_table)s,%(min_date)s,%(max_date)s,%(update_count)s,%(suffix)s);",
                sheet_message
            )
    return {"message": "数据上传成功!", "update_count": sheet_message["update_count"]}


""" 用户上传新表和更新表数据结束 """


@sheet_router.get("/variety/{variety_en}/sheet/", summary="用户获取品种数据表")
async def get_variety_sheet(
        user_token: str = Depends(oauth2_scheme),
        variety_en: str = Depends(verify_variety),
        group_id: int = Query(0, ge = 0),
        is_own: int = Query(0, ge = 0, le = 1)
):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        return {"message": "查询品种表成功!", "sheets": []}
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT st.id,DATE_FORMAT(st.create_time,'%%Y-%%m-%%d') AS create_date,"
            "DATE_FORMAT(st.update_time,'%%Y-%%m-%%d %%H:%%i') AS update_date,st.creator,st.update_by,"
            "st.variety_en,st.group_id,st.sheet_name,st.min_date,st.max_date,st.update_count,st.origin,"
            "st.note,st.is_private,"
            "(SELECT COUNT(id) FROM industry_user_chart WHERE st.id=sheet_id) AS chart_count "
            "FROM industry_user_sheet AS st "
            "WHERE st.variety_en=%s AND "
            "IF(0=%s,TRUE,st.group_id=%s) AND IF(0=%s,TRUE,st.creator=%s) AND IF(%s=st.creator,TRUE,st.is_private=0) "
            "ORDER BY st.suffix ASC;",
            (variety_en, group_id, group_id, is_own, user_id, user_id)
        )
        sheets = cursor.fetchall()
        cursor.execute("SELECT id,username FROM user_user WHERE role<>'normal';")
        user_list = cursor.fetchall()
        user_dict = {user_item["id"]: user_item["username"] for user_item in user_list}

    for sheet_item in sheets:
        sheet_item["creator"] = user_dict.get(sheet_item["creator"], "未知")
        sheet_item["update_by"] = user_dict.get(sheet_item["update_by"], "未知")
    return {"message": "查询数据表成功!", "sheets": sheets}


@sheet_router.get("/sheet/{sheet_id}/", summary="获取某个具体数据表数据")
async def sheet_source_values(sheet_id: int):
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT `id`,sheet_name,db_table FROM industry_user_sheet WHERE id=%s;", (sheet_id, )
        )
        sheet_info = cursor.fetchone()
    values = []
    if sheet_info:
        with VarietySheetDB() as cursor:
            cursor.execute(
                "SELECT * FROM %s;" % sheet_info["db_table"]
            )
            values = cursor.fetchall()
    return {"message": "数据查询成功!", "sheet_values": values}


@sheet_router.put("/sheet/suffix-swap/", summary="交换表排序后缀")
async def swap_sheet_suffix(
        swap_item: SwapSuffixItem = Body(...)
):
    with MySqlZ() as cursor:
        # 交换
        cursor.execute(
            "UPDATE industry_user_sheet AS sheet1 "
            "JOIN industry_user_sheet AS sheet2 "
            "ON sheet1.id=%s AND sheet2.id=%s "
            "SET sheet1.suffix=sheet2.suffix,sheet2.suffix=sheet1.suffix;",
            (swap_item.swap_id, swap_item.to_swap)
        )
    return {"message": "交换排序成功!", "swap_row": swap_item.swap_row}


def delete_variety_sheet(db_table):
    """ 删除数据表的原数据 """
    with VarietySheetDB() as cursor:
        cursor.execute("DROP TABLE %s;" % db_table)


@sheet_router.delete("/sheet/{sheet_id}/", summary="删除指定表")
async def delete_sheet(sheet_id: int, user_token: str = Depends(oauth2_scheme)):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unknown User")
    with MySqlZ() as cursor:
        # 查询数据表信息
        cursor.execute(
            "SELECT id,creator,db_table FROM industry_user_sheet "
            "WHERE id=%s;", (sheet_id, )
        )
        sheet_info = cursor.fetchone()
        if not sheet_info:
            raise HTTPException(status_code=400, detail="Unknown Sheet")
        if sheet_info["creator"] != user_id:
            # 用户删除的是别人的表
            # 查询用户的身份
            cursor.execute(
                "SELECT id,role FROM user_user WHERE id=%s;", (user_id,)
            )
            operator = cursor.fetchone()
            if not operator:
                raise HTTPException(status_code=401, detail="Unknown User")
            if operator["role"] not in ["superuser", "operator"]:
                # 查询用户的品种权限和本表所属品种
                cursor.execute(
                    "SELECT usersheet.id FROM industry_user_sheet AS usersheet "
                    "INNER JOIN user_user_variety AS uservariety "
                    "ON usersheet.variety_en=uservariety.variety_en "
                    "AND usersheet.id=%s AND uservariety.user_id=%s;",
                    (sheet_id, user_id)
                )
                user_auth_variety = cursor.fetchone()
                if not user_auth_variety:  # 用户没有该品种的权限,不能删除
                    raise HTTPException(status_code=403, detail="Can not Delete Sheet")
        # 如果是删除自己的表(或管理员删除),删除相应的原数据和已作图的表
        cursor.execute(
            "SELECT id,creator,option_file FROM industry_user_chart "
            "WHERE sheet_id=%s;", (sheet_id, )
        )
        sheet_charts = cursor.fetchall()
        for chart_item in sheet_charts:  # 删除数据图形和图形配置文件
            option_file = os.path.join(FILE_STORAGE, chart_item["option_file"])
            if os.path.exists(option_file):
                os.remove(option_file)
            cursor.execute("DELETE FROM industry_user_chart WHERE id=%s;", (chart_item["id"]))
        # 删除数据表
        delete_variety_sheet(sheet_info["db_table"])
        cursor.execute("DELETE FROM industry_user_sheet WHERE id=%s;", (sheet_id, ))
    return {"message": "删除成功!本表相关联数据已被清除."}


@sheet_router.post("/sheet/{sheet_id}/public/", summary="用户修改数据表是否公开")
async def modify_sheet_public(
        sheet_id: int,
        user_token=Depends(oauth2_scheme),
        is_private: int = Body(..., ge=0, le=1, embed=True)
):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        return {"message": "登录过期修改失败!"}
    with MySqlZ() as cursor:
        cursor.execute(
            "UPDATE industry_user_sheet SET is_private=%s "
            "WHERE id=%s AND creator=%s;", (is_private, sheet_id, user_id)
        )
    return {"message": "修改成功!"}


@sheet_router.put('/sheet/{sheet_id}/record/{record_id}/', summary='用户修改指定表下的指定记录')
async def modify_sheet_one_record(
        sheet_id: int, record_id: int,
        user_token: str = Depends(oauth2_scheme),
        record_item: dict = Body(...)
):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        return {"message": "登录过期修改失败!"}
    with MySqlZ() as m_cursor:
        # 查询数据表名称
        m_cursor.execute("SELECT id,db_table FROM industry_user_sheet WHERE id=%s;", sheet_id)
        sheet_obj = m_cursor.fetchone()
    if not sheet_obj:
        return {"message": "数据表不存在,修改失败!"}
    db_table = sheet_obj['db_table']
    # 修改对应的数据
    # 删除id列,对应生成update语句
    del record_item['id']
    u_sub_list = []
    for key, value in record_item.items():
        u_sub_list.append('{}="{}"'.format(key, value))
    # 转为字符串
    update_statement = "UPDATE %s SET %s WHERE id=%s;" % (db_table, ','.join(u_sub_list), record_id)
    with VarietySheetDB() as vs_cursor:
        vs_cursor.execute(update_statement)
    return {"message": "修改数据成功!"}


@sheet_router.get('/sheet/{sheet_id}/record/last/', summary='获取数据表的最新一行数据')
async def get_sheet_last_record(sheet_id: int):
    # 获取数据表的名称
    with MySqlZ() as cursor:
        cursor.execute("SELECT id,db_table FROM industry_user_sheet WHERE id=%s;", (sheet_id, ))
        table_obj = cursor.fetchone()
        if not table_obj:
            return {'message': '查询成功!', 'record': []}
        db_table = table_obj['db_table']
    # 获取最大日期的一行数据
    query_row = "SELECT * FROM {} WHERE column_0=(SELECT MAX(column_0) FROM {} WHERE id>1);".format(db_table, db_table)
    query_header = "SELECT * FROM {} WHERE id=1;".format(db_table)
    with VarietySheetDB() as vs_cursor:
        vs_cursor.execute(query_row)
        max_date_row = vs_cursor.fetchone()
        vs_cursor.execute(query_header)
        header_row = vs_cursor.fetchone()
    return {'message': '查询成功!', 'last_row': max_date_row, 'header_row': header_row}


@sheet_router.post('/sheet/{sheet_id}/record/add/', summary="用户为指定表添加记录")
async def add_sheet_record(sheet_id: int, user_token: str = Depends(oauth2_scheme),
                           body_data: list = Body(...)):
    # 解析用户
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        return {'message': '登录过期,修改失败!', 'new_count': 0}
    if len(body_data) < 1:
        return {'message': '添加成功!您没有增加数据', 'new_count': 0}
    # 检查上传者身份,并验证表的归属(pass)
    # 处理上传的数据
    columns = ['column_{}'.format(i) for i in range(len(body_data[0]))]
    # 转为pandas,去除重复日期的值
    df = pd.DataFrame(body_data, columns=columns)
    df.drop_duplicates(subset=['column_0'], inplace=True, keep='first')
    with MySqlZ() as cursor:
        cursor.execute("SELECT id,db_table FROM industry_user_sheet WHERE id=%s;", (sheet_id, ))
        sheet_obj = cursor.fetchone()
        if not sheet_obj:
            return {'message': '数据表不存在,添加错误!', 'new_count': 0}
        db_table = sheet_obj['db_table']
        with VarietySheetDB() as v_cursor:
            # 查询表头截取数据
            v_cursor.execute("SELECT * FROM %s WHERE id=1;" % db_table)
            sheet_headers_dict = v_cursor.fetchone()
            # 根据headers生成column列(防止新增列后出现的错误)
            columns_indexes = ["column_{}".format(i) for i in range(len(sheet_headers_dict) - 1)]  # 减1为id列
            # 截取数据
            df = df.reindex(columns=columns_indexes, fill_value='')
            add_count = 0
            if not df.empty:
                # 插入数据
                last_index = len(df.columns) - 1
                col_name = ""
                val_name = ""
                for index, col_item in enumerate(df.columns.values.tolist()):
                    if index == last_index:
                        col_name += col_item
                        val_name += "%(" + col_item + ")s"
                    else:
                        col_name += col_item + ","
                        val_name += "%(" + col_item + ")s" + ","
                new_values = df.to_dict(orient="records")
                insert_statement = "INSERT INTO %s (%s) VALUES (%s);" % (db_table, col_name, val_name)
                add_count = v_cursor.executemany(insert_statement, new_values)
            # 查询表的最大值和最小值
            v_cursor.execute(
                "SELECT MIN(column_0) AS min_date,MAX(column_0) AS max_date FROM %s WHERE id>2;" % db_table)
            date_msg = v_cursor.fetchone()
        if date_msg['min_date'] and date_msg['max_date']:
            # 更新表的信息
            sheet_message = {'min_date': date_msg['min_date'], 'max_date': date_msg['max_date']}
            sheet_message["update_by"] = user_id
            sheet_message["update_time"] = datetime.now()
            sheet_message['update_count'] = add_count
            sheet_message['db_table'] = db_table
            # 更新品种表的数据记录
            cursor.execute(
                "UPDATE industry_user_sheet SET update_by=%(update_by)s,update_time=%(update_time)s,"
                "min_date=%(min_date)s,max_date=%(max_date)s,update_count=%(update_count)s "
                "WHERE db_table=%(db_table)s;",
                sheet_message
            )
    return {'message': '添加数据成功!', 'new_count': add_count}

