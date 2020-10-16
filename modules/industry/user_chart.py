# _*_ coding:utf-8 _*_
# @File  : user_chart.py
# @Time  : 2020-09-08 9:08
# @Author: zizle

""" 图形相关
API-1: 保存一个图形的配置
API-2: 一张表内的所有图形(模板渲染)
API-3: 单个图形的配置和作图数据
API-4: 单个品种的所有图形列表(模板渲染/JSON)
API-5: 获取单个图形的基本信息(不是配置信息)
API-6: 修改单个图形的解读描述
API-7: 交换两个图形的排序后缀suffix
API-8: 修改图形主页显示与品种也显示与否
API-9: 删除图形及相关配置文件
"""
import re
import os
import json
import pandas as pd
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from utils.verify import oauth2_scheme, decipher_user_token
from utils.encryptor import generate_chart_option_filepath
from db.mysql_z import MySqlZ, VarietySheetDB
from configs import FILE_STORAGE, logger
from .models import ChartOption, SwapSuffixItem

chart_router = APIRouter()

# 挂载模板文件夹
template = Jinja2Templates(directory='templates')


# 验证品种
def verify_variety(variety_en: str):
    if not re.match(r'^[A-Z]{1,2}$', variety_en):
        raise HTTPException(detail="Invalidate Variety!", status_code=400)
    return variety_en


@chart_router.post("/sheet/{sheet_id}/chart/", summary="为一张表保存图形配置")
async def sheet_chart(
        sheet_id: int,
        user_token: str = Depends(oauth2_scheme),
        chart_option: ChartOption = Body(...)
):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token Expired!")
    if not all([chart_option.title, chart_option.variety_en, chart_option.option]):
        raise HTTPException(status_code=400, detail="Option Error!")
    relative_path = "ChartOption/{}".format(generate_chart_option_filepath(user_id))
    option_file = os.path.join(FILE_STORAGE, relative_path)
    # 创建文件夹
    file_folder = os.path.split(option_file)[0]
    if not os.path.exists(file_folder):
        os.makedirs(file_folder)
    with open(option_file, 'w', encoding='utf-8') as fp:
        json.dump(chart_option.option, fp, indent=4)
    # 保存到数据库
    save_dict = {
        "creator": user_id,
        "title": chart_option.title,
        "variety_en": chart_option.variety_en,
        "sheet_id": sheet_id,
        "option_file": relative_path,
        "decipherment": chart_option.decipherment,
        "is_private": 1 if chart_option.is_private else 0
    }
    try:
        with MySqlZ() as cursor:
            cursor.execute(
                "INSERT INTO industry_user_chart "
                "(creator,title,variety_en,sheet_id,option_file,decipherment,is_private) "
                "VALUES (%(creator)s,%(title)s,%(variety_en)s,%(sheet_id)s,%(option_file)s,"
                "%(decipherment)s,%(is_private)s);",
                save_dict
            )
            # 更新后缀
            new_id = cursor._instance.insert_id()
            cursor.execute("UPDATE industry_user_chart SET suffix=id WHERE id=%s;", (new_id,))
    except Exception as e:
        # 保存失败删除已保存的json文件
        if os.path.exists(option_file):
            os.remove(option_file)
        logger.error("用户保存图形配置失败:{}".format(e))
        return {"message": "保存图形失败"}
    else:
        return {"message": "保存图形配置成功!"}


@chart_router.get("/sheet/{sheet_id}/chart/", summary="获取一张表的所有图形信息")
async def get_sheet_charts(
        request: Request,
        sheet_id: int,
        is_own: int = Query(0, ge=0, le=1),
        token: str = Query('')
):
    user_id, _ = decipher_user_token(token)
    if not user_id:
        return {"message": "UnAuthenticated!"}
    # 查询这个表格所有图形信息
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id, DATE_FORMAT(create_time,'%%Y-%%m-%%d') AS create_time,creator,"
            "title,variety_en,sheet_id,option_file,decipherment,suffix,is_principal,is_petit "
            "FROM industry_user_chart "
            "WHERE IF(%s=creator,TRUE,is_private=0) AND IF(%s=0,TRUE,creator=%s) AND sheet_id=%s "
            "ORDER BY suffix ASC;",
            (user_id, is_own, user_id, sheet_id,)
        )
        charts = cursor.fetchall()
    return template.TemplateResponse(
        "sheet_charts.html",
        {
            "request": request,
            "has_chart": len(charts),
            "sheet_charts": charts
        }
    )


""" 返回图形配置和数据开始 """


def generate_days_of_year():
    """ 生成一年的每一月每一天 """
    days_list = list()
    start_day = datetime.strptime("2020-01-01", "%Y-%m-%d")
    end_day = datetime.strptime("2020-12-31", "%Y-%m-%d")
    while start_day <= end_day:
        days_list.append(start_day.strftime("%m-%d"))
        start_day += timedelta(days=1)
    return days_list


def get_season_chart_source(source_df):
    """ 处理季节图形的数据 """
    target_values = dict()  # 保存最终数据的字典
    target_values["xAxisData"] = generate_days_of_year()
    # 获取column_0的最大值和最小值
    min_date = source_df["column_0"].min()
    max_date = source_df["column_0"].max()
    start_year = int(min_date[:4])
    end_year = int(max_date[:4])
    for year in range(start_year, end_year + 1):
        # 获取当年的第一天和最后一天
        current_first = str(year) + "-01-01"
        current_last = str(year) + "-12-31"
        # 从data frame中取本年度的数据并转为列表字典格式
        current_year_df = source_df[(source_df["column_0"] >= current_first) & (source_df["column_0"] <= current_last)]
        current_year_df["column_0"] = current_year_df["column_0"].apply(lambda x: x[5:])
        target_values[str(year)] = current_year_df.to_dict(orient="record")
    return target_values


def sheet_data_handler(base_option, source_dataframe):
    """ 根据图形配置处理表格的数据 """
    chart_type = base_option["chart_category"]
    # 取数据的表头(表头名称用于作图时的图例)
    headers_df = source_dataframe.iloc[:1]
    # 将表头转为字典
    headers_dict = headers_df.to_dict(orient="record")[0]
    values_df = source_dataframe.iloc[2:]
    # 取最大值和最小值
    start_year = base_option["start_year"]
    end_year = base_option["end_year"]
    if start_year > "0":
        start_date = str(start_year) + "-01-01"
        # 切出大于开始日期的数据
        values_df = values_df[values_df["column_0"] >= start_date]
    if end_year > "0":
        # 切出小于结束日期的数据
        end_date = str(end_year) + "-12-31"  # 含结束年份end_year + 1
        values_df = values_df[values_df["column_0"] <= end_date]
    # 数据是否去0处理
    for series_item in base_option["series_data"]:
        column_index = series_item["column_index"]
        contain_zero = series_item["contain_zero"]
        if not contain_zero:  # 数据不含0,去0处理
            values_df = values_df[values_df[column_index] != "0"]
    values_df = values_df.sort_values(by="column_0")  # 最后进行数据从小到大的时间排序
    # table_show_df.reset_index(inplace=True)  # 重置索引,让排序生效(赋予row正确的值。可不操作,转为json后,索引无用处了)
    #
    # 普通图形返回结果数据
    if chart_type == "normal":
        # 处理横轴的格式
        date_length = base_option["x_axis"]["date_length"]
        values_df["column_0"] = values_df["column_0"].apply(lambda x: x[:date_length])
        values_json = values_df.to_dict(orient="record")
    elif chart_type == "season":  # 季节图形将数据分为{year1: values1, year2: values2}型
        values_json = get_season_chart_source(values_df.copy())
    else:
        values_json = []
    return values_json, headers_dict.copy()


@chart_router.get("/chart-option/{chart_id}/", summary="获取某个图形的配置和数据")
async def chart_option_values(chart_id: int):
    # 查询出表格和配置
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT charttb.id,charttb.title,charttb.option_file,sheettb.db_table "
            "FROM industry_user_chart AS charttb "
            "INNER JOIN industry_user_sheet AS sheettb "
            "ON charttb.sheet_id=sheettb.id AND charttb.id=%s;",
            (chart_id,)
        )
        chart_info = cursor.fetchone()
    if not chart_info:
        return {}
    # 获取配置
    option_file = os.path.join(FILE_STORAGE, chart_info["option_file"])
    if not os.path.exists(option_file):
        return {}
    with open(option_file, 'r') as fp:
        base_option = json.load(fp)
    # 查询出表的具体数据
    sheet_table = chart_info["db_table"]
    with VarietySheetDB() as cursor:
        cursor.execute("SELECT * FROM %s;" % sheet_table)
        sheet_data = cursor.fetchall()
    # 处理数据
    chart_values, headers_dict = sheet_data_handler(base_option, pd.DataFrame(sheet_data))
    return {"message": "获取数据成功!", "chart_type": base_option["chart_category"], "base_option": base_option,
            "chart_values": chart_values, "sheet_headers": headers_dict}


""" 返回图形配置和数据结束 """


@chart_router.get("/industry/chart/", summary="渲染主页的图形")
async def industry_chart(request: Request):
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id, DATE_FORMAT(create_time,'%%Y-%%m-%%d') AS create_time,creator,"
            "title,variety_en,sheet_id,option_file,decipherment,suffix,is_principal,is_petit "
            "FROM industry_user_chart WHERE is_principal='2' AND is_private=0;"
        )
        charts = cursor.fetchall()
    return template.TemplateResponse(
        "sheet_charts.html",
        {
            "request": request,
            "has_chart": len(charts),
            "sheet_charts": charts
        }
    )


@chart_router.get("/variety/{variety_en}/chart/", summary="获取品种的所有图形列表")
async def variety_chart(
        request: Request,
        variety_en: str = Depends(verify_variety),
        token: str = Query(''),
        is_own: int = Query(0, ge=0, le=1),
        render: int = Query(0, ge=0, le=1),
        is_petit: int = Query(0, ge=0, le=1)
):
    user_id, _ = decipher_user_token(token)
    if not user_id:
        return {"message": "UnAuthenticated!", "data": []}
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id, DATE_FORMAT(create_time,'%%Y-%%m-%%d') AS create_time,creator,"
            "title,variety_en,sheet_id,option_file,decipherment,suffix,is_principal,is_petit,is_private "
            "FROM industry_user_chart "
            "WHERE variety_en=%s AND IF(%s=0,TRUE,creator=%s) AND IF(%s=creator,TRUE,is_private=0) AND IF(%s=0,TRUE,is_petit=1) "
            "ORDER BY suffix ASC;",
            (variety_en, is_own, user_id, user_id, is_petit)
        )
        charts = cursor.fetchall()
        cursor.execute("SELECT id,username FROM user_user WHERE role<>'normal';")
        user_list = cursor.fetchall()
        user_dict = {user_item["id"]: user_item["username"] for user_item in user_list}

    for chart_item in charts:
        chart_item["creator"] = user_dict.get(chart_item["creator"])

    if render:  # 模板渲染
        return template.TemplateResponse(
            "sheet_charts.html",
            {
                "request": request,
                "has_chart": len(charts),
                "sheet_charts": charts
            }
        )
    else:
        return {"message": "获取图形信息成功!", "data": charts}


@chart_router.get("/chart/{chart_id}/", summary="获取图形的基本信息")
async def chart_base_info(chart_id: int):
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT title,variety_en,decipherment,suffix "
            "FROM industry_user_chart WHERE id=%s;", (chart_id,)
        )
        chart = cursor.fetchone()

    return {"message": "查询成功!", "data": chart}


@chart_router.put("/chart-decipherment/{chart_id}/", summary="修改图形的解读信息")
async def chart_decipherment(
        chart_id: int,
        decipherment: str = Body(..., embed=True)
):
    with MySqlZ() as cursor:
        cursor.execute(
            "UPDATE industry_user_chart SET decipherment=%s WHERE id=%s;", (decipherment, chart_id)
        )
    return {"message": "修改成功!"}


@chart_router.put("/chart/suffix-swap/", summary="交换图形排序后缀")
async def swap_chart_suffix(
        swap_item: SwapSuffixItem = Body(...)
):
    with MySqlZ() as cursor:
        # 交换
        cursor.execute(
            "UPDATE industry_user_chart AS sheet1 "
            "JOIN industry_user_chart AS sheet2 "
            "ON sheet1.id=%s AND sheet2.id=%s "
            "SET sheet1.suffix=sheet2.suffix,sheet2.suffix=sheet1.suffix;",
            (swap_item.swap_id, swap_item.to_swap)
        )
    return {"message": "交换排序成功!", "swap_row": swap_item.swap_row}


@chart_router.put("/chart/{chart_id}/display/", summary="修改图形在主页或品种页显示或仅自己可见")
async def chart_display(
        chart_id: int,
        user_token=Depends(oauth2_scheme),
        is_principal: int = Query(0, ge=0, le=2),
        is_petit: int = Query(0, ge=0, le=1),
        is_private: int = Query(0, ge=0, le=1)
):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="UnKnown User.")
    with MySqlZ() as cursor:
        cursor.execute(
            "UPDATE industry_user_chart SET is_principal=%s,is_petit=%s,is_private=%s WHERE id=%s;",
            (str(is_principal), is_petit, is_private, chart_id)
        )
    return {"message": "设置成功!"}


@chart_router.delete("/chart/{chart_id}/", summary="用户删除图形")
async def delete_chart(
        chart_id: int,
        user_token: str = Depends(oauth2_scheme)
):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unknown User")
    # 查询图形信息
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,creator,option_file FROM industry_user_chart WHERE id=%s;", (chart_id, )
        )
        chart_info = cursor.fetchone()
        if not chart_info:
            raise HTTPException(status_code=400, detail="Unknown Chart")
        if chart_info["creator"] != user_id:
            # 查询操作用户信息
            cursor.execute(
                "SELECT id,role FROM user_user WHERE id=%s;", (user_id, )
            )
            operator = cursor.fetchone()
            if not operator or operator["role"] not in ["superuser", "operator"]:
                raise HTTPException(status_code=403, detail="Can not Delete Chart ")
        # 删除图形和配置
        option_file = os.path.join(FILE_STORAGE, chart_info["option_file"])
        if os.path.exists(option_file):
            os.remove(option_file)
        cursor.execute("DELETE FROM industry_user_chart WHERE id=%s;", (chart_id, ))
        return {"message": "删除成功!"}

