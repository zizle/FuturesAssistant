# _*_ coding:utf-8 _*_
# @File  : AutoMoveReports.py
# @Time  : 2020-11-19 08:11
# @Author: zizle
""" 自动分类报告并移动报告到指定位置 """
import os
import re
import time
import json
import datetime
import random
import string
import shutil
import logging
from pymysql.connections import Connection
from pymysql.cursors import DictCursor

with open("autoConfig.json", "r", encoding="utf8") as fp:
    configs = json.load(fp)

MATCH_REG = configs["MATCH_REG"]
MATCH_TYPE = configs["MATCH_TYPE"]

# 微信自动保存的文件
FILE_FOLDER = configs["WECHAT_FOLDER"]  # 微信自动保存的文件路径
FILE_STORAGE = configs["FILE_STORAGE"]  # 系统文件夹

APP_DIR = configs["APP_DIR"]
params = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "mysql",
    "database": "futures_assistant"
}

# 日志记录
def logger_handler(app_dir, log_level):
    # 日志配置
    log_folder = os.path.join(app_dir, "logs/")
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    log_file_name = time.strftime('%Y-%m-%d', time.localtime(time.time())) + '.log'
    log_file_path = log_folder + os.sep + log_file_name

    handler = logging.FileHandler(log_file_path, encoding='UTF-8')
    handler.setLevel(log_level)
    logger_format = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(logger_format)
    return handler


logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logger_handler(app_dir=APP_DIR, log_level=logging.INFO))


def generate_unique_filename(file_folder, filename):
    filepath = os.path.join(file_folder, "{}.pdf".format(filename))
    abs_filepath = os.path.join(FILE_STORAGE, filepath)
    if os.path.exists(abs_filepath):
        new_filename_suffix = ''.join(random.sample(string.ascii_letters, 6))
        new_filename = "{}_{}".format(filename, new_filename_suffix)
        return generate_unique_filename(file_folder, new_filename)
    else:
        return file_folder, filename


# 数据库连接


class MySqlZ(Connection):
    """ 系统主数据库 """
    def __init__(self):
        super(MySqlZ, self).__init__(**params)
        self.execute_cursor = self.cursor(DictCursor)
        self.execute_cursor._instance = self

    def __enter__(self):
        """Context manager that returns a Cursor"""
        if self.open:
            self.begin()
            return self.execute_cursor
        else:
            raise ConnectionError("连接Mysql失败!")

    def __exit__(self, exc, value, traceback):
        """On successful exit, commit. On exception, rollback"""
        if exc:
            self.rollback()
        else:
            self.commit()
        self.execute_cursor.close()
        self.close()


# 读取文件夹中所有报告
def find_files(path, replace_str, files_list):
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
            # print("----------:",time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_info.st_mtime)))
            files_list.append(
                {
                    "relative_path": fn, "filename": os.path.split(fn)[1],
                    "file_size": str(round(file_info.st_size / (1024 * 1024), 2)) + "MB",
                    "create_time":  time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_info.st_mtime))
                },
            )
        else:
            find_files(temp_path, replace_str, files_list)
    return files_list


def read_all_reports():
    file_list = find_files(FILE_FOLDER, FILE_FOLDER, [])
    ready_add = []
    # 将文件分类
    for file_item in file_list:
        # filename = re.sub(r'^\d-', '', file_item["filename"])  # 替换数字开头的文件名称
        filename = file_item["filename"]
        if os.path.splitext(filename)[1] != ".pdf":
            continue
        variety_en = ""
        for match_str in MATCH_REG:
            if filename.find(match_str) != -1:
                variety_en = MATCH_REG[match_str]
                break
        if variety_en:
            file_type = ""
            # 确定是周报还是日报
            for type_item in MATCH_TYPE:
                if filename.find(type_item) != -1:
                    file_type = MATCH_TYPE[type_item]
                    break
            if file_type:
                # 进行数据的入库和转移
                file_item["variety_en"] = variety_en
                file_item["report_type"] = file_type
                ready_add.append(file_item)

    return ready_add


def add_report(files):
    logger.info("得到待处理文件 {} 个.".format(len(files)))
    if not files:
        return
    # 创建数据库记录
    with MySqlZ() as cursor:
        # 将数据添加入库(以文件的创建日期为报告日期)
        for index, file_item in enumerate(files):
            relative_path = file_item["relative_path"]
            filepath = os.path.join(FILE_FOLDER, relative_path)  # 原文件所在路径
            filename = os.path.split(filepath)[1]
            title = os.path.splitext(filename)[0]
            title = re.sub(r'^\d-', '', title)  # 替换数字开头的文件名称
            variety_en = file_item["variety_en"].split(';')[0]
            file_source_date = datetime.datetime.strptime(file_item["create_time"], "%Y-%m-%d %H:%M:%S")
            date_folder = file_source_date.strftime("%Y-%m")  # 以月为单位保存
            filedate = file_source_date.strftime("%Y-%m-%d")
            # 创建新文件所在路径
            save_folder = "REPORTS/{}/{}/{}/".format(variety_en, file_item["report_type"], date_folder)
            # 新名称
            save_folder, new_filename = generate_unique_filename(save_folder, title)
            filename = "{}.pdf".format(new_filename)
            report_folder = os.path.join(FILE_STORAGE, save_folder)
            if not os.path.exists(report_folder):
                os.makedirs(report_folder)
            report_path = os.path.join(report_folder, filename)
            sql_path = os.path.join(save_folder, filename)
            # print(filepath)
            # print(report_path)
            # print(sql_path)
            cursor.execute(
                "SELECT id,filepath FROM research_report WHERE filepath=%s;", (sql_path,)
            )
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO research_report (`date`,creator,variety_en,title,report_type,filepath) "
                    "VALUES (%s,%s,%s,%s,%s,%s);",
                    (filedate, 1, file_item["variety_en"], title, file_item["report_type"], sql_path)
                )
                shutil.move(filepath, report_path)  # 将文件移动到目标位置
                logger.info("处理文件{}:{} 成功!".format(index + 1, file_item["relative_path"]))
            time.sleep(0.2)


def enter_handler():
    now = datetime.datetime.now()
    if now.strftime("%H:%M") > "16:30":
        return True
    else:
        return False


while True:
    if enter_handler():
        logger.info("程序启动处理报告!")
        ready_adds = read_all_reports()
        add_report(ready_adds)
        logger.info("报告处理完毕!")
    time.sleep(90)
