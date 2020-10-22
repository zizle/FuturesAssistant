# _*_ coding:utf-8 _*_
# @File  : user_tables.py
# @Time  : 2020-08-31 11:53
# @Author: zizle

from db.mysql_z import MySqlZ


with MySqlZ() as cursor:
    # 用户数据表
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `user_user` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`join_time` DATETIME NOT NULL DEFAULT NOW(),"
        "`recent_login` DATETIME NOT NULL DEFAULT NOW(),"
        "`user_code` VARCHAR(20) NOT NULL,"
        "`username` VARCHAR(128) NOT NULL DEFAULT '',"
        "`phone` VARCHAR(11) NOT NULL UNIQUE,"
        "`email` VARCHAR(50) DEFAULT '',"
        "`password_hashed` VARCHAR(32) NOT NULL,"
        "`role` ENUM('superuser','operator','collector','research','normal') NOT NULL DEFAULT 'normal',"
        "`avatar` VARCHAR(256) NOT NULL DEFAULT '',"
        "`is_active` BIT DEFAULT 1,"
        "`note` VARCHAR(8) NOT NULL DEFAULT ''"
        ") DEFAULT CHARSET='utf8';"
    )
    # 添加一个超级管理员
    cursor.execute(
        "INSERT INTO `user_user` (user_code,username,phone,password_hashed,role,note) "
        "VALUES ('user_SuperAdmin','超级管理员','18866668888','7f4675985509569cd50a96d129a196ff','superuser','超级管理员');"
    )
    # 用户的在线时间
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `user_user_online` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`user_id` INT(11) NOT NULL,"
        "`update_time` DATETIME NOT NULL DEFAULT NOW() ON UPDATE NOW(),"
        "`online_date` VARCHAR(10) NOT NULL,"
        "`total_online` INT(11) DEFAULT 0"
        ") DEFAULT CHARSET='utf8';"
    )
    # 用户可登录的客户端
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `user_user_client` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`user_id` INT(11) NOT NULL,"
        "`client_id` INT(11) NOT NULL,"
        "`expire_date` VARCHAR(10) NOT NULL"
        ") DEFAULT CHARSET='utf8';"
    )

    # 用户有权限的模块(module_text模块是在前端设置的,记录名称)
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `user_user_module` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`user_id` INT(11) NOT NULL,"
        "`module_id` VARCHAR(20) NOT NULL,"
        "`module_text` VARCHAR(20) NOT NULL,"
        "`expire_date` VARCHAR(10) NOT NULL"
        ") DEFAULT CHARSET='utf8';"
    )

    # 用户有权限的品种(variety_en方便权限查询使用)
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `user_user_variety` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`user_id` INT(11) NOT NULL,"
        "`variety_id` VARCHAR(20) NOT NULL,"
        "`variety_en` VARCHAR(2) NOT NULL,"
        "`expire_date` VARCHAR(10) NOT NULL"
        ") DEFAULT CHARSET='utf8';"
    )

    # 用户的信息扩展表(微信ID)
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `user_user_extension` ("
        "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
        "`user_id` INT(11) NOT NULL,"
        "`wx_id` VARCHAR(22) NOT NULL"
        ") DEFAULT CHARSET='utf8';"
    )
