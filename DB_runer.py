# -*- coding: utf-8 -*-
"""
Author  : Hanlei Jin
Date    : 2023/9/11
E-mail  : jin@smail.swufe.edu.cn
"""
import random
import time
import traceback

from db_utils.crawler.get_dblp import get_publ
from db_utils.crawler.crawl_utils import set_logger
from db_utils.mongo_utils import MongoHandler
from db_utils.mysql_utils import MysqlHandler


def create_ccf_table():
    MysqlHandler().write_ccf()


def crawl_and_save(ccf):
    """
        ccf:(`url`, `type`, `abbr`, `name`)
    """
    mh = MongoHandler()
    count = 0
    errors = []
    logger = set_logger()
    logger.info("***** Crawler START*****")
    for url, ccf_name in ccf:
        if "dblp" not in url:
            continue
        is_conf = 1 if "conf" in url else 0
        try:
            flag = mh.find_all_flag(ccf_name)
            papers = get_publ(url=url, is_conf=is_conf, flag=flag)
            if papers:
                mh.write_papers(ccf_name, papers)
            logger.info(f"{ccf_name} DONE!")
        except:
            ex = traceback.format_exc()
            logger.info(f"ERROR - {ccf_name}")
            logger.info(ex)
            errors.append(ccf)
        time.sleep(random.random()*3)
        if count % 7 == 0:
            time.sleep(random.random()*20)


def create_dblp_db():
    ccf = MysqlHandler().read_ccf_url()
    crawl_and_save(ccf)


if __name__ == '__main__':
    create_ccf_table()
    create_dblp_db()

