# _*_ coding:utf-8 _*_
# @File  : product.py
# @Time  : 2021-01-19 10:25
# @Author: zizle

# 产品服务模块相关数据库表

from db.mysql_z import MySqlZ

with MySqlZ() as cursor:
    # 顾问服务数据表
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `product_consultant` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`create_time` INT NOT NULL COMMENT '创建日期',"
        "`update_time` INT NOT NULL COMMENT '更新日期',"
        "`article_type` VARCHAR(32) NOT NULL DEFAULT '' COMMENT '类型',"
        "`content` TEXT NOT NULL COMMENT '内容',"
        "`author_id` INT NOT NULL COMMENT '作者'"
        ") DEFAULT CHARSET='utf8';"
    )

    # 交易策略数据表
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `product_strategy` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`create_time` INT NOT NULL COMMENT '创建日期',"
        "`update_time` INT NOT NULL COMMENT '更新日期',"
        "`content` VARCHAR(1024) NOT NULL COMMENT '内容',"
        "`author_id` INT NOT NULL COMMENT '作者'"
        ") DEFAULT CHARSET='utf8';"
    )

    # 投资方案和套保方案数据表
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `product_plan_file` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`create_time` INT NOT NULL COMMENT '创建日期',"
        "`creator` INT NOT NULL DEFAULT 0 COMMENT '创建者',"
        "`variety_en` VARCHAR(20) DEFAULT '' COMMENT '关联品种',"
        "`title` VARCHAR(128) NOT NULL COMMENT '文件名称',"
        "`file_type` INT NOT NULL COMMENT '类型',"
        "`filepath` VARCHAR(512) NOT NULL UNIQUE COMMENT '文件URL'"
        ") DEFAULT CHARSET='utf8';"
    )

