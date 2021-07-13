-- 系统数据库 --

------------------------- DAT_daily_quotes 【期货日行情】 --------------------------------

CREATE TABLE IF NOT EXISTS `dat_futures_daily_quotes` (
`id` INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '期货日行情',
`create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
`update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
`creator` INT NOT NULL DEFAULT 0 COMMENT '创建者',
`quotes_ts` INT NOT NULL COMMENT '日期时间戳',
`variety_en` VARCHAR(2) NOT NULL COMMENT '品种',
`contract` VARCHAR(6) NOT NULL COMMENT '合约',
`pre_settlement` DOUBLE(16,3) NOT NULL DEFAULT 0 COMMENT '前结算价',
`open_price` DOUBLE(16,3) NOT NULL DEFAULT 0 COMMENT '开盘价',
`highest` DOUBLE(16,3) NOT NULL DEFAULT 0 COMMENT '最高价',
`lowest` DOUBLE(16,3) NOT NULL DEFAULT 0 COMMENT '最低价',
`close_price` DOUBLE(16,3) NOT NULL DEFAULT 0 COMMENT '收盘价',
`settlement` DOUBLE(16,3) NOT NULL DEFAULT 0 COMMENT '结算价',
`trade_volume` DOUBLE(16,3) NOT NULL DEFAULT 0 COMMENT '成交量',
`trade_price` DOUBLE(16,3) NOT NULL DEFAULT 0 COMMENT '成交额',
`position_volume` DOUBLE(16,3) NOT NULL DEFAULT 0 COMMENT '持仓量',
`increase_volume` DOUBLE(16,3) NOT NULL DEFAULT 0 COMMENT '持仓增减',
`is_active` BIT NOT NULL DEFAULT 1 COMMENT '有效',
UNIQUE KEY `dtvn`(`quotes_ts`,`contract`)
) DEFAULT CHARSET='utf8mb4';

------------------------- DAT_daily_rank 【期货日持仓排名】 --------------------------------

CREATE TABLE IF NOT EXISTS `dat_futures_daily_rank` (
`id` INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '期货日持仓',
`create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
`update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
`creator` INT NOT NULL DEFAULT 0 COMMENT '创建者',
`rank_ts` INT NOT NULL COMMENT '日期时间戳',
`variety_en` VARCHAR(2) NOT NULL COMMENT '品种',
`contract` VARCHAR(6) NOT NULL COMMENT '合约',
`rank` TINYINT UNSIGNED NOT NULL COMMENT '排名',
`trade_company` VARCHAR(16) NOT NULL DEFAULT '' COMMENT '成交量公司',
`trade` INT NOT NULL DEFAULT 0 COMMENT '成交量',
`trade_increase` INT NOT NULL DEFAULT 0 COMMENT '成交增量',
`long_position_company` VARCHAR(16) NOT NULL DEFAULT '' COMMENT '多单公司',
`long_position` INT NOT NULL DEFAULT 0 COMMENT '多单量',
`long_position_increase` INT NOT NULL DEFAULT 0 COMMENT '多单增量',
`short_position_company` VARCHAR(16) NOT NULL DEFAULT '' COMMENT '空单公司',
`short_position` INT NOT NULL DEFAULT 0 COMMENT '空单量',
`short_position_increase` INT NOT NULL DEFAULT 0 COMMENT '空单增量',
`is_active` BIT NOT NULL DEFAULT 1 COMMENT '有效',
UNIQUE KEY `rcr`(`rank_ts`,`contract`, `rank`)
) DEFAULT CHARSET='utf8mb4';

------------------------- DAT_index_position 【期货指数持仓】 --------------------------------
--- 主力价格指数 | 品种价格与持仓乘积和 | 持仓量和  | 20多单量 | 20空单量 ------------
--- 当contract=variety_en时,position_volume为各合约的持仓和,position_price为各合约持仓与收盘价乘积和--

CREATE TABLE IF NOT EXISTS `dat_futures_price_position` (
`id` INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '期货指数持仓',
`create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
`update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
`creator` INT NOT NULL DEFAULT 0 COMMENT '创建者',
`quotes_ts` INT NOT NULL COMMENT '日期时间戳',
`variety_en` VARCHAR(2) NOT NULL COMMENT '品种',
`contract` VARCHAR(6) NOT NULL COMMENT '主力合约',
`close_price` DOUBLE(16,3) NOT NULL COMMENT '收盘价',
`position_price` DOUBLE(16,3) NOT NULL COMMENT '持仓价格汇总',
`position_volume` INT NOT NULL COMMENT '总持仓',
`long_position`  INT NOT NULL DEFAULT 0 COMMENT '20多单量',
`short_position` INT NOT NULL DEFAULT 0 COMMENT '20空单量',
`is_active` BIT NOT NULL DEFAULT 1 COMMENT '有效',
UNIQUE KEY `dtc`(`quotes_ts`,`contract`)
) DEFAULT CHARSET='utf8mb4';
