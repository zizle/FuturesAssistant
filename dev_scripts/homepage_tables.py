# _*_ coding:utf-8 _*_
# @File  : homepage_tables.py
# @Time  : 2020-10-12 15:36
# @Author: zizle

from db.mysql_z import MySqlZ
with MySqlZ() as cursor:
    # 广告记录表
    # image: 图片在服务器中的位置
    # filepath: 文件所在的相对路径
    # web_url: 使用默认浏览器打开的url
    # content: 直接显示内容的
    # is_active: 启用
    # note: 备注
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `homepage_advertisement` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`title` VARCHAR (256) NOT NULL,"
        "`ad_type` ENUM('file','web','content') NOT NULL,"
        "`image` VARCHAR (512) NOT NULL,"
        "`filepath` VARCHAR (512) NOT NULL DEFAULT '',"
        "`web_url` VARCHAR (512) NOT NULL DEFAULT '',"
        "`content` VARCHAR (512) NOT NULL DEFAULT '',"
        "`note` VARCHAR (128) NOT NULL DEFAULT '',"
        "`is_active` BIT NOT NULL DEFAULT 0"
        ") DEFAULT CHARSET='utf8';"
    )
