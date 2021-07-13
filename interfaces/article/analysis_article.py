# _*_ coding:utf-8 _*_
# @File  : analysis_article.py
# @Time  : 2021-05-31 15:11
# @Author: zizle
# 分析文章
import datetime
import hashlib
import os

from fastapi import APIRouter, Body, UploadFile, Form, Depends, HTTPException, Query, Path

from utils.authorization import logged_require
from utils.file import generate_unique_filename
from utils.constant import VARIETY_ZH
from db import FAConnection
from configs import FILE_STORAGE

analysis_article_api = APIRouter()


@analysis_article_api.post('/analysis/', summary='创建一篇分析文章')
async def create_analysis_article(file: UploadFile = Body(None), user_data: tuple = Depends(logged_require),
                                  title: str = Form(...), web_url: str = Form(''), variety: str = Form(...),
                                  create_time: str = Form(...)):
    if not user_data[0]:
        raise HTTPException(status_code=401, detail="Unknown User")
    try:
        create_time = datetime.datetime.strptime(create_time, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        raise HTTPException(status_code=400, detail='时间格式错误, %Y-%m-%d %H:%M:%S')
    if file:
        # 保存文件,并添加数据库记录
        # 创建保存的文件夹
        date_folder = datetime.datetime.now().strftime('%Y%m%d')[:6]  # 以月为单位保存
        # 创建新文件所在路径
        save_folder = "ARTICLE/{}/{}/".format(user_data[0], date_folder)
        report_folder = os.path.join(FILE_STORAGE, save_folder)
        if not os.path.exists(report_folder):
            os.makedirs(report_folder)
        now_name = hashlib.md5(str(datetime.datetime.now().timestamp()).encode('utf8')).hexdigest()
        save_folder, new_filename, _ = generate_unique_filename(save_folder, now_name, 'pdf')
        filename = "{}.pdf".format(new_filename)
        report_path = os.path.join(report_folder, filename)
        sql_path = os.path.join(save_folder, filename)
        # 保存文件
        content = await file.read()  # 将文件保存到目标位置
        with open(report_path, "wb") as fp:
            fp.write(content)
        await file.close()
        params = [create_time, user_data[0], title, '', sql_path, variety]
    else:
        params = [create_time, user_data[0], title, web_url, '', variety]
        # 添加数据库记录
        if not web_url:
            raise HTTPException(status_code=400, detail='参数错误')
    db = FAConnection()
    sql = 'INSERT INTO product_article (create_time,creator,title,web_url,file_url,varieties) ' \
          'VALUES (%s,%s,%s,%s,%s,%s)'
    success = db.execute(sql, params)
    if success:
        return {'message': '创建成功!'}
    else:
        raise HTTPException(status_code=400, detail='创建失败了!')


@analysis_article_api.get('/analysis/', summary='分页获取分析文章')
async def get_analysis_article(page: int = Query(1, ge=1), page_size: int = Query(30, le=100)):
    record_start = (page - 1) * page_size
    record_offset = page_size
    db = FAConnection()
    sql = 'SELECT SQL_CALC_FOUND_ROWS id,create_time,title,web_url,file_url,varieties ' \
          'FROM product_article ' \
          'WHERE is_active=1 ' \
          'ORDER BY create_time DESC LIMIT %s,%s;'
    records = db.query(sql, [record_start, record_offset], keep_conn=True)
    # 查询总记录数
    total_obj = db.query('SELECT FOUND_ROWS() AS total;', fetchone=True)[0]
    total_count = total_obj['total'] if total_obj else 1  # 当前总页码
    total_page = (total_count + page_size - 1) // page_size

    for item in records:
        item['create_date'] = item['create_time'].strftime('%Y-%m-%d')
        item['article_type'] = '分析文章'
        item['variety_name'] = ','.join([VARIETY_ZH.get(i, i) for i in item['varieties'].split(',')])
    return {'message': '查询成功!', 'articles': records, 'page': page, 'page_size': page_size, 'total_page': total_page}


@analysis_article_api.put('/analysis/{article_id}/', summary='修改一条分析文章记录')
async def update_article_item(article_id: int = Path(..., ge=1), item: dict = Body(...)):
    db = FAConnection()
    sql = 'UPDATE product_article SET reading=reading+1 WHERE id=%s LIMIT 1;'
    db.execute(sql, [article_id])
    return {'message': '修改成功!'}



