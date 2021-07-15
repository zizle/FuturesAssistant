-- 基础支持数据库

------------------------- SYSTEM 【菜单表】 --------------------------------

CREATE TABLE IF NOT EXISTS `sys_menu` (
`id` INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '菜单表',
`create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
`update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
`creator` INT NOT NULL COMMENT '创建者',
`parent_id` INT NOT NULL DEFAULT 0 COMMENT '父级',
`category` TINYINT UNSIGNED NOT NULL COMMENT '类别',
`icon` VARCHAR(16) NOT NULL DEFAULT '' COMMENT '图标名',
`name_en` VARCHAR(60) NOT NULL UNIQUE COMMENT '英文',
`name_zh` VARCHAR(60) NOT NULL COMMENT '中文',
`sorted` INT NOT NULL COMMENT '排序',
`is_active` BIT NOT NULL DEFAULT 1 COMMENT '有效'
) DEFAULT CHARSET='utf8mb4';

INSERT INTO sys_menu(creator,parent_id,category,name_en,name_zh,sorted) VALUES(1,0,1,'menu_manage','菜单管理',0);
INSERT INTO sys_menu(creator,parent_id,category,name_en,name_zh,sorted) VALUES(1,1,1,'system_menu','系统菜单',1);

------------------------- SYSTEM 【上市品种表】 --------------------------------

CREATE TABLE IF NOT EXISTS `sys_variety` (
`id` INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '品种表',
`create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
`update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
`creator` INT NOT NULL COMMENT '创建者',
`category` TINYINT UNSIGNED NOT NULL COMMENT '类别',
`exchange` TINYINT UNSIGNED NOT NULL COMMENT '交易所',
`variety_code` CHAR(2) NOT NULL COMMENT '交易代码',
`variety_name` VARCHAR(60) NOT NULL COMMENT '中文',
`is_active` BIT NOT NULL DEFAULT 1 COMMENT '有效',
UNIQUE KEY `exvc`(`exchange`,`variety_code`)
) DEFAULT CHARSET='utf8mb4';


------------------------- SYSTEM 【用户表】 --------------------------------

CREATE TABLE IF NOT EXISTS `sys_person` (
`id` INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '用户表',
`create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
`update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
`creator` INT UNSIGNED NOT NULL COMMENT '创建者',
`username` VARCHAR(128) NOT NULL COMMENT '用户名',
`nickname` VARCHAR(32) NOT NULL DEFAULT '' COMMENT '昵称',
`account` VARCHAR(32) NOT NULL UNIQUE COMMENT '账号',
`phone` CHAR(11) NOT NULL DEFAULT '' COMMENT '手机号',
`password` VARCHAR(60) NOT NULL COMMENT '密码',
`grouping` TINYINT UNSIGNED NOT NULL COMMENT '用户组别',
`is_active` BIT NOT NULL DEFAULT 1 COMMENT '有效'
) DEFAULT CHARSET='utf8mb4';


------------------------- SYSTEM 【用户表-品种权限】 --------------------------------

CREATE TABLE IF NOT EXISTS `sys_person_variety` (
`id` INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '用户品种权限',
`create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
`update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
`creator` INT UNSIGNED NOT NULL COMMENT '创建者',
`user_id` INT UNSIGNED NOT NULL COMMENT '用户ID',
`variety_id` INT UNSIGNED NOT NULL COMMENT '品种ID',
`expire` DATE NOT NULL COMMENT '有效期',
`is_active` BIT NOT NULL DEFAULT 1 COMMENT '有效',
UNIQUE KEY `uvariety`(`user_id`,`variety_id`)
) DEFAULT CHARSET='utf8mb4';
