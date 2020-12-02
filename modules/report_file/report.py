# _*_ coding:utf-8 _*_
# @File  : report.py
# @Time  : 2020-09-30 13:34
# @Author: zizle

""" 管理报告的API
API-1: 网络上传报告文件
API-2: 条件查询报告（按日期）
API-3: 条件查询报告(分页)
API-4: 删除报告
API-5: 修改报告的基本信息
API-6: 修改报告名称
API-7: 首页日报获取最新5-50个信息
"""
import os
import string
import random
import shutil
from datetime import datetime
from fastapi import APIRouter, Depends, Form, UploadFile, HTTPException, Query, Body
from utils.verify import oauth2_scheme, decipher_user_token
from db.mysql_z import MySqlZ
from utils.constant import VARIETY_ZH, REPORT_TYPES
from .models import ReportType, ModifyReportInfo
from configs import FILE_STORAGE

report_router = APIRouter()


def generate_unique_filename(file_folder, filename):
    filepath = os.path.join(file_folder, "{}.pdf".format(filename))
    abs_filepath = os.path.join(FILE_STORAGE, filepath)
    if os.path.exists(abs_filepath):
        new_filename_suffix = ''.join(random.sample(string.ascii_letters, 6))
        new_filename = "{}_{}".format(filename, new_filename_suffix)
        return generate_unique_filename(file_folder, new_filename)
    else:
        return file_folder, filename


@report_router.post("/report-file/", summary="上传报告文件")
async def create_report(
        user_token: str = Depends(oauth2_scheme),
        report_file: UploadFile = Form(...),
        date: str = Form(...),
        relative_varieties: str = Form(...),
        report_type: str = Form(...),
        rename_text: str = Form('')
):
    # 从网络上传的文件信息保存报告
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unknown User")
    # 验证report_type:
    if report_type not in ["daily", "weekly", "monthly", "annual", "special", "others"]:
        raise HTTPException(status_code=400, detail="Unknown Report Type")
    # 创建保存的文件夹
    date_folder = date[:7]  # 以月为单位保存
    variety_en = relative_varieties.split(';')[0]
    # 创建新文件所在路径
    save_folder = "REPORTS/{}/{}/{}/".format(variety_en, report_type, date_folder)
    report_folder = os.path.join(FILE_STORAGE, save_folder)
    if not os.path.exists(report_folder):
        os.makedirs(report_folder)
    filename = report_file.filename
    title = os.path.splitext(filename)[0]
    if rename_text:  # 重名名,需检测重命名结果是否已存在,如果存在需再生成新的结果,否则文件将被直接覆盖
        title = rename_text
        save_folder, new_filename = generate_unique_filename(save_folder, title)
        filename = "{}.pdf".format(new_filename)
    report_path = os.path.join(report_folder, filename)
    sql_path = os.path.join(save_folder, filename)
    # 创建数据库记录
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,filepath FROM research_report WHERE filepath=%s;", (sql_path, )
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO research_report (`date`,creator,variety_en,title,report_type,filepath) "
                "VALUES (%s,%s,%s,%s,%s,%s);",
                (date, user_id, relative_varieties, title, report_type, sql_path)
            )
        content = await report_file.read()      # 将文件保存到目标位置
        with open(report_path, "wb") as fp:
            fp.write(content)
        await report_file.close()
    return {"message": "上传成功!"}


@report_router.get("/report-file/paginator/", summary="条件获取报告信息(分页)")
async def get_report_with_paginator(
        report_type: str = Query(...),
        variety_en: str = Query("0"),
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=10, le=1000)
):
    # 验证report_type:
    if report_type not in REPORT_TYPES.keys():
        raise HTTPException(status_code=400, detail="Unknown Report Type")

    if variety_en == "0":
        execute_sql = "SELECT id,`date`,variety_en,title,report_type,filepath,is_active FROM research_report " \
                      "WHERE report_type=%s ORDER BY `date` DESC,`id` DESC LIMIT %s,%s;"
        execute_params = (report_type, (page-1)*page_size, page_size)
        count_execute_sql = "SELECT COUNT(id) AS total_count FROM research_report " \
                            "WHERE report_type=%s;"
        count_execute_params = (report_type, )
    else:
        execute_sql = "SELECT id,`date`,variety_en,title,report_type,filepath,is_active FROM research_report " \
                      "WHERE report_type=%s AND LOCATE(%s,variety_en) > 0 " \
                      "ORDER BY `date` DESC,`id` DESC LIMIT %s,%s;"
        execute_params = (report_type, variety_en, (page-1)*page_size, page_size)
        count_execute_sql = "SELECT COUNT(id) AS total_count FROM research_report " \
                            "WHERE report_type=%s AND LOCATE(%s,variety_en) > 0;"
        count_execute_params = (report_type, variety_en)
    with MySqlZ() as cursor:
        cursor.execute(execute_sql, execute_params)
        reports = cursor.fetchall()
        # 查询总量
        cursor.execute(count_execute_sql, count_execute_params)
        total_count = cursor.fetchone()["total_count"]
    # 计算总页码
    total_page = int((total_count + page_size - 1) / page_size)
    # 处理类型和品种名
    for report_item in reports:
        report_item["type_text"] = REPORT_TYPES.get(report_item["report_type"], report_item["report_type"])
        # report_item["variety_zh"] = VARIETY_ZH.get(report_item["variety_en"], report_item["variety_en"])
        report_item["variety_zh"] = ';'.join([VARIETY_ZH.get(item, item) for item in report_item["variety_en"].split(";")])

    return {"message": "查询成功!", "reports": reports, "page": page, "page_size": page_size, "total_page": total_page}


@report_router.get("/report-file/", summary="条件查询报告信息(按日期)")
async def get_report_info(
        query_date: str = Query(...),
        report_type: str = Query(...),
        variety_en: str = Query('0')
):
    # 验证report_type:
    if report_type not in REPORT_TYPES.keys():
        raise HTTPException(status_code=400, detail="Unknown Report Type")
    with MySqlZ() as cursor:
        if variety_en == '0':
            cursor.execute(
                "SELECT id,`date`,variety_en,title,report_type,filepath,is_active FROM research_report "
                "WHERE `date`=%s AND report_type=%s;",
                (query_date, report_type)
            )
        else:
            cursor.execute(
                "SELECT id,`date`,variety_en,title,report_type,filepath,is_active FROM research_report "
                "WHERE `date`=%s AND report_type=%s AND LOCATE(%s,variety_en) > 0;",
                (query_date, report_type, variety_en)
            )
        reports = cursor.fetchall()
    # 处理文件名
    for report_item in reports:
        report_item["filename"] = os.path.split(report_item["filepath"])[1]
        report_item["type_text"] = REPORT_TYPES.get(report_item["report_type"], report_item["report_type"])
        report_item["variety_zh"] = VARIETY_ZH.get(report_item["variety_en"], report_item["variety_en"])
    return {"message": "查询成功!", "reports": reports}


@report_router.put("/report-file/{report_id}/", summary="修改报告的基本信息")
async def change_report_info(
        report_id: int,
        user_token: str = Depends(oauth2_scheme),
        report_item: ModifyReportInfo = Body(...)
):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unknown User")
    # 根据信息修改相应信息
    if report_item.date is not None:
        # 验证日期
        try:
            t_date = datetime.strptime(report_item.date, "%Y-%m-%d").strftime("%Y-%m-%d")
        except Exception:
            pass
        else:
            # 修改报告日期
            with MySqlZ() as cursor:
                cursor.execute("UPDATE research_report SET `date`=%s WHERE id=%s AND creator=%s;", (t_date, report_id, user_id))
        return {"message": "修改日期成功!"}
    if report_item.variety_en is not None:
        # 修改报告关联品种
        with MySqlZ() as cursor:
            cursor.execute("UPDATE research_report SET variety_en=%s WHERE id=%s AND creator=%s;", (report_item.variety_en, report_id, user_id))
        return {"message": "修改关联品种成功!"}
    if report_item.title is not None:
        # 查询原报告信息
        with MySqlZ() as cursor:
            cursor.execute("SELECT id,filepath FROM research_report WHERE id=%s;", (report_id,))
            old_item = cursor.fetchone()
            if report_item:  # 报告存在
                filepath = old_item["filepath"]
                folder, old_name = os.path.split(filepath)
                old_filename = os.path.join(FILE_STORAGE, filepath)
                new_folder, new_filename = generate_unique_filename(folder, report_item.title)
                new_filepath = os.path.join(new_folder, "{}.pdf".format(new_filename))
                new_filepath = new_filepath.replace("\\", "/")  # 修改windows系统的分隔符，结果为sql路径
                new_filename = os.path.join(FILE_STORAGE, new_filepath)
                # 修改名称
                cursor.execute(
                    "UPDATE research_report SET title=%s,filepath=%s WHERE id=%s AND creator=%s;",
                    (report_item.title, new_filepath, report_id, user_id)
                )
                os.rename(old_filename, new_filename)  # 放在修改数据库后,防止重命名失败而数据库修改了
        return {"message": "修改名称成功!"}
    if report_item.report_type is not None:
        if report_item.report_type not in REPORT_TYPES.keys():
            pass
        else:
            # 修改报告的类型
            with MySqlZ() as cursor:
                # 查询文件所在位置
                cursor.execute("SELECT id,report_type,filepath FROM research_report WHERE id=%s;", (report_id, ))
                report_obj = cursor.fetchone()
                if report_obj:
                    old_relative_path_list = report_obj["filepath"].split('/')
                    old_relative_path_list[2] = report_item.report_type
                    new_relative_path = '/'.join(old_relative_path_list)
                    old_abs_path = os.path.join(FILE_STORAGE, report_obj["filepath"])
                    new_abs_path = os.path.join(FILE_STORAGE, new_relative_path)
                    new_folder, new_filename = os.path.split(os.path.splitext(new_abs_path)[0])
                    # 目标文件夹中若存在文件需生成唯一的文件名称
                    new_folder, new_filename = generate_unique_filename(new_folder, new_filename)
                    # 新的文件绝对路径
                    new_abs_path = os.path.join(new_folder, "{}.pdf".format(new_filename))
                    new_abs_path = new_abs_path.replace('\\', '/')
                    # 得到新的相对路径
                    new_relative_path = new_abs_path.replace(FILE_STORAGE, '')
                    # 新的文件夹若不存在需创建
                    new_folder = os.path.split(new_abs_path)[0]
                    if not os.path.exists(new_folder):
                        os.makedirs(new_folder)
                    # 更新数据库并移动文件
                    cursor.execute(
                        "UPDATE research_report SET report_type=%s,filepath=%s WHERE id=%s;",
                        (report_item.report_type, new_relative_path, report_id)
                    )
                    # 移动文件
                    shutil.move(old_abs_path, new_abs_path)
            return {"message": "修改类型成功!"}
    if report_item.is_active is not None:
        with MySqlZ() as cursor:
            cursor.execute(
                "UPDATE research_report SET is_active=IF(is_active=0,1,0) "
                "WHERE creator=%s AND id=%s;", (user_id, report_id)
            )
        return {"message": "修改公开成功!"}

    return {"message": "修改成功!什么也没改变!"}


@report_router.put("/report-filename/{report_id}/", summary="修改报告名称")
async def modify_report_filename(report_id: int, user_token: str = Depends(oauth2_scheme), filename: str = Query(...)):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unknown User")
    with MySqlZ() as cursor:
        # 查出本报告文件所在的位置
        cursor.execute("SELECT id,filepath FROM research_report WHERE id=%s;", (report_id, ))
        report_item = cursor.fetchone()
        if report_item:
            filepath = report_item["filepath"]
            folder, old_name = os.path.split(filepath)
            old_filename = os.path.join(FILE_STORAGE, filepath)
            new_filepath = os.path.join(folder, filename)
            new_filepath = new_filepath.replace("\\", "/")  # 修改windows系统的分隔符，结果为sql路径
            new_filename = os.path.join(FILE_STORAGE, new_filepath)
            # 修改文件名
            new_title = os.path.splitext(filename)[0]
            cursor.execute("UPDATE research_report SET title=%s,filepath=%s WHERE id=%s;", (new_title, new_filepath, report_id))
            os.rename(old_filename, new_filename)  # 放在修改数据库后,防止重命名失败而数据库修改了


@report_router.delete("/report-file/{report_id}/")
async def delete_report_file(
        report_id: int,
        user_token: str = Depends(oauth2_scheme),
):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unknown User")

    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,filepath,creator FROM research_report WHERE id=%s;", (report_id, )
        )
        report_info = cursor.fetchone()
        if not report_info:
            raise HTTPException(status_code=400, detail="Unknown Report")
        # 是否是创建者删除
        if report_info["creator"] != user_id:
            # 查询用户是否是管理员
            cursor.execute("SELECT id,role FROM user_user WHERE id=%s;", (user_id, ))
            user_info = cursor.fetchone()
            if not user_info:
                raise HTTPException(status_code=401, detail="Unknown User")
            if user_info["role"] not in ["superuser", "operator"]:
                return {"message": "不能删除别人上传的报告!"}
        # 删除报告
        cursor.execute(
            "DELETE FROM research_report WHERE id=%s;", (report_id, )
        )
        report_path = os.path.join(FILE_STORAGE, report_info["filepath"])
        if os.path.exists(report_path) and os.path.isfile(report_path):
            os.remove(report_path)
    return {"message": "删除成功!"}


@report_router.get("/latest-report/", summary="灵活获取最新5-50个报告")
async def get_report(report_type: ReportType = Query(...), count: int = Query(..., ge=5, le=50)):
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT `date`,variety_en,title,report_type,filepath "
            "FROM research_report "
            "WHERE report_type=%s AND is_active=1 "
            "ORDER BY `date` DESC,`id` DESC LIMIT %s;",
            (report_type, count)
        )
        reports = cursor.fetchall()
    for report_item in reports:
        report_item["type_zh"] = REPORT_TYPES.get(report_item["report_type"], report_item["report_type"])
        report_item["variety_zh"] = VARIETY_ZH.get(report_item["variety_en"], report_item["variety_en"])
    return {"message": "获取最新{}成功!".format(REPORT_TYPES.get(report_type)), "reports": reports}
