# _*_ coding:utf-8 _*_
# @File  : advertisement.py
# @Time  : 2020-10-13 13:48
# @Author: zizle
""" 广告相关API
1- 创建一个新的广告
"""
import os
from fastapi import APIRouter, Form, UploadFile, Depends, HTTPException, Query
from utils.verify import oauth2_scheme, decipher_user_token
from utils.encryptor import generate_random_filename
from db.mysql_z import MySqlZ
from configs import FILE_STORAGE
ad_router = APIRouter()


@ad_router.post("/advertisement/", summary="创建一个新的广告")
async def create_advertisement(
        user_token: str = Depends(oauth2_scheme),
        image: UploadFile = Form(...),
        pdf_file: UploadFile = Form(None),
        title: str = Form(...),
        ad_type: str = Form(...),
        web_url: str = Form(''),
        content: str = Form(''),
        note: str = Form(''),
):
    # 验证用户写入数据库
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unknown User")
    # 验证ad_type
    if ad_type not in ["file", "web", "content"]:
        raise HTTPException(status_code=400, detail="Unknown Advertisement Type!")
    # 创建广告文件保存的文件夹
    image_folder = os.path.join(FILE_STORAGE, "ADVERTISEMENT/Image/")
    file_folder = os.path.join(FILE_STORAGE, "ADVERTISEMENT/File/")
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
    if not os.path.exists(file_folder):
        os.makedirs(file_folder)
    # 生成filename
    image_filename = generate_random_filename() + ".png"
    image_path = os.path.join(image_folder, image_filename)
    image_sql_path = os.path.join("ADVERTISEMENT/Image/", image_filename)
    pdf_path, pdf_sql_path = '', ''
    if pdf_file:
        pdf_filename = generate_random_filename() + ".pdf"
        pdf_path = os.path.join(file_folder, pdf_filename)
        pdf_sql_path = os.path.join("ADVERTISEMENT/File/", pdf_filename)
    # 数据保存并入库
    with MySqlZ() as cursor:
        cursor.execute("SELECT id,role FROM user_user WHERE id=%s;", (user_id, ))
        user_info = cursor.fetchone()
        if not user_info or user_info["role"] not in ["superuser", "operator"]:
            raise HTTPException(status_code=400, detail="没有权限进行这个操作!")
        # 将数据保存起来并入库
        cursor.execute(
            "INSERT INTO homepage_advertisement(title,ad_type,image,filepath,web_url,content,note) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s);",
            (title, ad_type, image_sql_path, pdf_sql_path, web_url, content, note)
        )
        # 保存文件
        image_content = await image.read()  # 将文件保存到目标位置
        with open(image_path, "wb") as fp:
            fp.write(image_content)
        await image.close()
        if pdf_file:
            pdf_content = await pdf_file.read()
            with open(pdf_path, "wb") as fp:
                fp.write(pdf_content)
            await pdf_file.close()
    return {"message": "创建新广告成功!"}


@ad_router.get("/advertisement/", summary="获取系统中所有广告信息")
async def get_advertisements(is_active: int = Query(1, ge=0, le=1)):
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,title,ad_type,image,filepath,web_url,content,note,is_active "
            "FROM homepage_advertisement WHERE IF(%s=0,TRUE,is_active=%s);", (is_active, is_active)
        )
        advertisements = cursor.fetchall()
        return {"message": "查询成功!", "advertisements": advertisements}


@ad_router.put("/advertisement/{ad_id}/", summary="修改广告的启用与否")
async def modify_advertisement_active(ad_id: int):
    with MySqlZ() as cursor:
        cursor.execute(
            "UPDATE homepage_advertisement SET is_active=IF(is_active=1,0,1) WHERE id=%s;",
            (ad_id, )
        )
        return {"message": "修改成功!"}
