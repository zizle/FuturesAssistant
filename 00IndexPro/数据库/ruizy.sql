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
