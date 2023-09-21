# -*- coding: utf-8 -*-
"""
Author  : Hanlei Jin
Date    : 2023/9/13
E-mail  : jin@smail.swufe.edu.cn
"""
import re

import pymongo
from typing import List, Dict
from settings import MONGO_SERVER_IP, MONGO_SERVER_PORT


class MongoClass:
    def __init__(self):
        self.conn = pymongo.MongoClient(MONGO_SERVER_IP, MONGO_SERVER_PORT)
        self.db = self.conn["ccf2019"]


class MongoHandler:
    """
        Mongo写入内容
    """

    def __init__(self):
        self.db = MongoClass().db
        self.publs = self.db.list_collection_names()

    def check_col(self, publ):
        """
            检查出版物是否已在mongo中
        """
        return 1 if publ in self.publs else 0

    def write_papers(self, publ, papers: List[Dict]):
        col = self.db[publ]
        col.insert_many(papers)

    def remove_duplicates(self):
        for pulb in self.publs:
            col = self.db[pulb]
            urls = col.distinct("url")

            for url in urls:
                data = col.find_one({'url': url})
                col.delete_many({'url': url})
                col.insert_one(data)

    def find_all_flag(self, publ):
        col = self.db[publ]
        flags = col.distinct("url")
        return flags

    def search_paper(self, begin_year, end_year, selected_publ, keywords: str, is_strict):
        res = []
        keywords = re.sub(";|\s+;\s+", "|", keywords)
        max_count = len(keywords.split("|"))
        for publ in selected_publ:
            counts = []
            paper_of_publ = []
            col = self.db[publ]
            papers = col.find({"year": {"$gte": str(begin_year), "$lte": str(end_year)}},
                              {"_id": 0, "year": 1, "papers": 1})
            for titles in papers:
                try:
                    for title in titles["papers"]:
                        pattern = re.compile(keywords, re.I)
                        hits = re.findall(pattern, title)
                        count = len(set(hits))
                        if count:
                            paper_of_publ.append({"publ": publ, "year": titles["year"], "title": title, "count": count})
                            counts.append(count)
                except:
                    print(titles["papers"])
                # 按关键字数量排序
                if is_strict:
                    paper_of_publ_order = [paper_of_publ[i] for i in range(len(counts)) if counts[i] == max_count]
                else:
                    idx = sorted(range(len(counts)), key=lambda k: counts[k], reverse=True)
                    paper_of_publ_order = [paper_of_publ[i] for i in idx]
                res.extend(paper_of_publ_order)
        return res
