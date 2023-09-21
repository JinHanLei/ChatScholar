# -*- coding: utf-8 -*-
"""
Author  : Hanlei Jin
Date    : 2023/8/2
E-mail  : jin@smail.swufe.edu.cn
"""
import logging


def set_logger():
    # 格式化日志
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
    # 打开指定的文件并将其用作日志记录流
    file_handler = logging.FileHandler("logs.log")
    file_handler.setFormatter(formatter)
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger = logging.getLogger("DBLP Crawler")
    logger.addHandler(file_handler)
    logger.addHandler(console)
    logger.setLevel(logging.INFO)
    return logger
