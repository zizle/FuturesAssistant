# _*_ coding:utf-8 _*_
# @File  : user_folder.py
# @Time  : 2020-09-29 08:10
# @Author: zizle
from fastapi import APIRouter, Depends, Body, HTTPException, Query
from utils.verify import oauth2_scheme, decipher_user_token
from utils.client import encryption_uuid
from db.mysql_z import MySqlZ
from .models import UpdateFolderItem
folder_router = APIRouter()


@folder_router.post("/industry/user-folder/", summary="用户配置更新文件夹")
async def create_update_folder(
        user_token: str = Depends(oauth2_scheme),
        body_item: UpdateFolderItem = Body(...)
):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unknown User")
    body_item.client = encryption_uuid(body_item.client)  # 加密改变uuid与客户端数据库对应
    # 查询增加或更新
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,user_id FROM industry_user_folder "
            "WHERE client=%s AND user_id=%s AND variety_en=%s AND group_id=%s;",
            (body_item.client, user_id, body_item.variety_en, body_item.group_id)
        )
        is_exist = cursor.fetchone()
        if is_exist:  # 存在则更新
            cursor.execute(
                "UPDATE industry_user_folder SET folder=%s "
                "WHERE client=%s AND variety_en=%s AND group_id=%s AND user_id=%s;",
                (body_item.folder_path, body_item.client, body_item.variety_en, body_item.group_id, user_id)
            )
        else:
            cursor.execute(
                "INSERT INTO industry_user_folder (variety_en,group_id,folder,client,user_id) "
                "VALUES (%s,%s,%s,%s,%s);",
                (body_item.variety_en, body_item.group_id, body_item.folder_path, body_item.client, user_id)
            )
    return {"message": "配置成功!"}


@folder_router.get("/industry/user-folder/", summary="查询用户配置更新文件夹")
async def get_update_folder(
        user_token: str = Depends(oauth2_scheme),
        variety_en: str = Query(...),
        group_id: int = Query(0, ge=0),
        client: str = Query('', min_length=36, max_length=36)
):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unknown User")
    client = encryption_uuid(client)  # 加密uuid与数据库对应
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT varitytb.variety_name,grouptb.group_name,foldertb.folder "
            "FROM industry_user_folder AS foldertb,basic_variety AS varitytb,industry_sheet_group AS grouptb "
            "WHERE foldertb.variety_en=varitytb.variety_en "
            "AND foldertb.group_id=grouptb.id AND "
            "foldertb.client=%s AND foldertb.variety_en=%s AND foldertb.user_id=%s AND "
            "IF(%s=0,TRUE,foldertb.group_id=%s);",
            (client, variety_en, user_id, group_id, group_id)
        )
        folders = cursor.fetchall()
    return {"message": "查询成功!", "folders": folders}

