# _*_ coding:utf-8 _*_
# @File  : wechat_file.py
# @Time  : 2020-09-29 16:19
# @Author: zizle
""" 微信自动保存的文件 """
import os
import time
import shutil
from datetime import datetime
from fastapi import APIRouter, Path, Depends, Body, HTTPException
from fastapi.responses import FileResponse
from utils.verify import oauth2_scheme, decipher_user_token
from db.mysql_z import MySqlZ
from configs import WECHAT_FILE_PATH, FILE_STORAGE
from .models import ReportFileItem

wechat_file_router = APIRouter()


def verify_date_time(date_time):
    try:
        datetime.strptime(date_time, "%Y-%m-%d")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d")
    return date_time


def find_files(path, replace_str, files_list):
    """ 递归获取文件 """
    fsinfo = os.listdir(path)
    for fn in fsinfo:
        temp_path = os.path.join(path, fn)
        if not os.path.isdir(temp_path):
            # 解析出文件名称
            filename_suffix = os.path.splitext(temp_path)[1]
            if filename_suffix not in [".pdf", ".PDF"]:
                continue
            fn = temp_path.replace(replace_str, '')
            fn = '/'.join(fn.split('\\'))
            file_info = os.stat(temp_path)
            files_list.append(
                {
                    "relative_path": fn, "filename": os.path.split(fn)[1],
                    "file_size": str(round(file_info.st_size / (1024 * 1024), 2)) + "MB",
                    "create_time":  time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_info.st_ctime))
                },
            )
        else:
            find_files(temp_path, replace_str, files_list)


@wechat_file_router.get("/wechat-files/", summary="获取微信自动保存的文件信息")
async def get_wechat_files():
    # 获取符合的文件
    file_list = list()
    find_files(WECHAT_FILE_PATH, WECHAT_FILE_PATH, file_list)
    return {"message": "查询成功!", "file_list": file_list}


@wechat_file_router.get("/wechat-files/{relative_path:path}", summary="查看文件内容")
async def get_wechat_file(relative_path: str = Path(...)):
    filepath = os.path.join(WECHAT_FILE_PATH, relative_path)
    filename = os.path.split(relative_path)[1]
    if os.path.exists(filepath) and os.path.isfile(filepath):
        return FileResponse(filepath, filename=filename)


@wechat_file_router.delete("/wechat-files/{relative_path:path}", summary="删除微信自动保存的文件")
async def delete_wechat_files(relative_path: str = Path(...)):
    # 不做真正删除,只是将其移动到回收文件夹(可手动登录服务器回收)
    filepath = os.path.join(WECHAT_FILE_PATH, relative_path)  # 原文件所在路径
    recycle_folder = os.path.join(FILE_STORAGE, "RECYCLE_FILES/WechatFiles/")  # 目标回收站文件夹
    recycle_path = os.path.join(recycle_folder, relative_path)  # 目标文件路径
    if not os.path.exists(os.path.split(recycle_path)[0]):
        os.makedirs(os.path.split(recycle_path)[0])
    shutil.move(filepath, recycle_path)
    return {"message": "删除成功!"}


@wechat_file_router.post("/wechat-files/{relative_path:path}", summary="移动微信自动保存的文件")
async def create_report_with_wechat_files(
        user_token: str = Depends(oauth2_scheme),
        relative_path: str = Path(...),
        file_item: ReportFileItem = Body(...)
):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unknown User")
    file_item.date = verify_date_time(file_item.date)  # 验证处理datetime时间
    # 验证report_type:
    if file_item.report_type not in ["daily", "weekly", "monthly", "annual", "special", "others"]:
        raise HTTPException(status_code=400, detail="Unknown Report Type")
    # 从微信自动保存的文件信息创建报告,
    # 报告的相对文件路径(日报日期精确到日): REPORTS/{variety_en}/{report_type}/{年-月[-日]}/xxx.pdf
    filepath = os.path.join(WECHAT_FILE_PATH, relative_path)  # 原文件所在路径
    filename = os.path.split(filepath)[1]
    # 新名称
    if file_item.rename_text:
        filename = file_item.rename_text + ".pdf"
    title = os.path.splitext(filename)[0]
    variety_en = file_item.relative_varieties.split(';')[0]
    date_folder = file_item.date[:7]  # 以月为单位保存
    # 创建新文件所在路径
    save_folder = "REPORTS/{}/{}/{}/".format(variety_en, file_item.report_type, date_folder)
    report_folder = os.path.join(FILE_STORAGE, save_folder)
    if not os.path.exists(report_folder):
        os.makedirs(report_folder)
    report_path = os.path.join(report_folder, filename)
    sql_path = os.path.join(save_folder, filename)
    # 创建数据库记录
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,filepath FROM research_report WHERE filepath=%s;", (sql_path,)
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO research_report (`date`,creator,variety_en,title,report_type,filepath) "
                "VALUES (%s,%s,%s,%s,%s,%s);",
                (file_item.date, user_id, file_item.relative_varieties, title, file_item.report_type, sql_path)
            )
        shutil.move(filepath, report_path)  # 将文件移动到目标位置

    return {"message": "操作成功!"}
