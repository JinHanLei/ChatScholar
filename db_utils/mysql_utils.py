# -*- coding: utf-8 -*-
"""
Author  : Hanlei Jin
Date    : 2023/9/13
E-mail  : jin@smail.swufe.edu.cn
"""
import re
import pandas as pd
import pymysql
from settings import *


class MysqlClass:
    def __init__(self):
        self.conn = pymysql.connect(host=MYSQL_SERVER_IP,
                                    port=MYSQL_SERVER_PORT,
                                    user=MYSQL_USER_NAME,
                                    password=MYSQL_USER_PWD,
                                    db=MYSQL_DB_NAME,
                                    charset='utf8')

    def exec(self, sql):
        self.conn.ping(reconnect=True)
        cs = self.conn.cursor()
        cs.execute(sql)
        self.conn.commit()
        cs.close()
        self.conn.close()
        return True

    def save(self, table, data: dict):
        fields = self.getFields(data)
        value = self.getValue(data)
        sql = "INSERT INTO %s(%s) VALUES (%s)" % (table, fields, value)
        self.conn.ping(reconnect=True)
        cs = self.conn.cursor()
        cs.execute(sql)
        self.conn.commit()
        cs.close()
        self.conn.close()
        return True

    def getValue(self, data):
        """
            单引号'用于字符串，反引号`用于表名
        """
        value = ''
        for key in data:
            v = str(data[key])
            if value == '':
                value = "'" + v + "'"
            else:
                value = value + ",'" + v + "'"
        return value

    def getFields(self, data):
        fields = ""
        for key in data:
            if fields == '':
                fields = '`' + key + '`'
            else:
                fields = fields + ",`" + key + '`'
        return fields

    def findLastOne(self, table):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * from %s order by id desc limit 1" % (table))
        data = cursor.fetchone()
        cursor.close()
        self.conn.close()
        return data

    def search(self, sql, find_flag=0):
        """
            sql: "select xx from xx where xx"
        """
        cursor = self.conn.cursor()
        cursor.execute(sql)
        if find_flag == 0:
            data = cursor.fetchall()
        else:
            data = cursor.fetchone()
        cursor.close()
        self.conn.close()
        return data


class MysqlHandler:
    def __init__(self):
        self.mysql = MysqlClass()

    def create_ccf_bak(self):
        """
            创建MySQL信息表，初始化时使用，表中有内容时慎运行
            research_field:
            类型1-计算机体系结构/并行与分布计算/存储系统中，A/B/C类期刊会议共87个，其中4个非dblp数据库，为['Performance Evaluation: An International Journal', 'HOT CHIPS', 'JETTA', 'JGC']
            类型2-计算机网络中，A/B/C类期刊会议共52个，其中0个非dblp数据库
            类型3-网络与信息安全中，A/B/C类期刊会议共56个，其中4个非dblp数据库，为['TOPS', 'CLSR' , 'IFIP WG 11.9', 'HotSec']
            类型4-软件工程/系统软件/程序设计语言中，A/B/C类期刊会议共87个，其中1个非dblp数据库，为['QRS']
            类型5-数据库/数据挖掘/内容检索中，A/B/C类期刊会议共46个，其中1个非dblp数据库，为['JGITM']
            类型6-计算机科学理论中，A/B/C类期刊会议共51个，其中0个非dblp数据库
            类型7-计算机图形学与多媒体中，A/B/C类期刊会议共54个，其中2个非dblp数据库，为['JASA', 'CAVW']
            类型8-人工智能中，A/B/C类期刊会议共101个，其中3个非dblp数据库，为['JSLHR', 'IET-CVI', 'IET Signal Processing']
            类型9-人机交互与普适计算中，A/B/C类期刊会议共34个，其中1个非dblp数据库，为['CollaborateCom']
            类型10-交叉/综合/新兴中，A/B/C类期刊会议共38个，其中4个非dblp数据库，为['Cognition', 'CogSci', 'ISMB', 'IET Intelligent Transport Systems']
        """
        self.mysql.exec("DROP TABLE IF EXISTS {}".format(CCF_BAK_TABLE_NAME))
        self.mysql.exec("""CREATE TABLE `{}` (
                                  `_id` int(5) unsigned NOT NULL,
                                  `abbr` varchar(50) DEFAULT '' COMMENT '期刊会议名称缩写',
                                  `name` varchar(500) DEFAULT '' COMMENT '全称',
                                  `final_name` varchar(500) DEFAULT '' COMMENT '无缩写则用全称代替',
                                  `publisher` varchar(200) DEFAULT '' COMMENT '出版社',
                                  `url` varchar(200) DEFAULT '' COMMENT '期刊会议网址',
                                  `rank` varchar(1) DEFAULT 0 COMMENT '期刊会议等级',
                                  `joc` int(1) DEFAULT 0 COMMENT '期刊or会议:0-Journal,1-Conference',
                                  `category` int(2) DEFAULT 0 COMMENT '领域',
                                  PRIMARY KEY (`_id`) USING BTREE,
                                  UNIQUE KEY `publication` (`final_name`,`publisher`) USING BTREE
                                ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='CCF2019'"""
                        .format(CCF_BAK_TABLE_NAME))
        """
              `last_flag` int(8) DEFAULT NULL COMMENT '爬虫爬取的截止年份或期号',
              似乎没有必要
        """

    def create_ccf(self):
        """
            创建MySQL信息表，慎运行
        """
        self.mysql.exec("DROP TABLE IF EXISTS {}".format(CCF_TABLE_NAME))
        self.mysql.exec("alter table {} rename to {}".format(CCF_BAK_TABLE_NAME, CCF_TABLE_NAME))
        print("CCF TABLE CREATED!")

    def process_ccf(self):
        """
            去除完全重复的条目。url删去index.html，改http:为https:
        """
        ccf = pd.read_csv(CCF_FILE).drop('id', axis=1)
        ccf["url"] = ccf["url"].apply(lambda x: re.sub("index\.html", "", x).replace("http:", "https:").strip())
        ccf["name"] = ccf["name"].apply(lambda x: re.sub("\"", "", x).replace("\'", "\\'").strip())
        ccf["rank"] = ccf["rank"].apply(lambda x: x.strip())
        # 0-Journal,1-Conference
        ccf["joc"] = ccf["joc"].map({"Journal": 0, "Conference": 1})
        ccf["final_name"] = ccf["abbr"].fillna(ccf["name"])
        ccf.drop_duplicates(subset=["final_name", "publisher"], inplace=True)
        return ccf

    def write_ccf(self):
        ccf = self.process_ccf()
        self.create_ccf_bak()
        for row in ccf.itertuples():
            self.mysql.save(CCF_BAK_TABLE_NAME,
                            {
                                "_id": row.Index,
                                "abbr": row.abbr,
                                "name": row.name,
                                "final_name": row.final_name,
                                "publisher": row.publisher,
                                "url": row.url,
                                "rank": row.rank,
                                "joc": row.joc,
                                "category": row.category,
                            })
        self.create_ccf()

    def read_ccf_name(self, rank):
        """
            查找ccf期刊会议名、等级
        """
        res = self.mysql.search("select `final_name` from {} where `rank`='{}'".format(CCF_TABLE_NAME, rank))
        return [i[0] for i in res]

    def read_ccf_url(self):
        """
            用于爬虫,获取url和表名
        """
        res = self.mysql.search("select `url`, `final_name` from {}".format(CCF_TABLE_NAME))
        return res

    def read_ccf_class(self, _class="A"):
        """

        """
        res = self.mysql.search("select `abbr`, `name` from {} where `class`={}".format(CCF_TABLE_NAME, _class))
        ccf_class = []
        for each in res:
            ccf_class.append((each[0] if each[0] != "nan" else each[1], each[2]))
        return ccf_class
