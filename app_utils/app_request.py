# -*- coding: utf-8 -*-
"""
Author  : Hanlei Jin
Date    : 2023/9/16
E-mail  : jin@smail.swufe.edu.cn
"""
import json
import os
import re
import shutil
import gradio as gr
import requests
import pandas as pd
from app_utils.xunfei_request import SparkGPT
from pdf_utils.pdf_reader import PDFReader
from settings import API_IP, API_PORT, CHATGLM_ADDRESS

API_PATH = f"http://{API_IP}:{API_PORT}/"


def login(u, p):
    return gr.State({"state": True, "uname": u}) if u == "jin" and p == "jin" else gr.State(
        {"state": False, "uname": "游客"})


def search_paper(begin_year, end_year, selected_publ, keywords, is_strict):
    assert keywords
    if begin_year > end_year:
        begin_year = begin_year + end_year
        end_year = begin_year - end_year
        begin_year = begin_year - end_year
    data_bin = {"begin_year": begin_year, "end_year": end_year, "selected_publ": selected_publ,
                "keywords": keywords, "is_strict": is_strict}
    res = requests.post(API_PATH + "search", json=data_bin).json()["res"]
    if res:
        res = pd.DataFrame(res)
        if not os.path.exists("./temp/"):
            os.mkdir("./temp/")
        outputPath = "./temp/papers.csv"
        res.to_csv(outputPath, index=False)
        res["title"] = res["title"].apply(
            lambda x: f"<a href=\"https://www.semanticscholar.org/search?q={x}\" target=\"_blank\">{x}</a>")
        return res.to_html(index=False, escape=False), "共计{}篇".format(len(res)), outputPath
    else:
        return "", "未找到结果", "./temp/empty.txt"


def get_ccf():
    return requests.get(API_PATH + "ccf").json()["res"]


def get_one_bib(title):
    data_bin = {"title": title}
    res = requests.post(API_PATH + "bib", json=data_bin).json()["res"]
    return res


def generate_file(file_obj):
    if file_obj:
        file_obj = file_obj[0]
        tmpdir = "temp/"
        shutil.copy(file_obj.name, tmpdir)
        FileName = os.path.basename(file_obj.name)
        NewfilePath = os.path.join(tmpdir, FileName)
        return gr.State(NewfilePath)


def generate_bib_file(file_obj):
    if file_obj:
        tmpdir = "temp/"
        shutil.copy(file_obj.name, tmpdir)
        FileName = os.path.basename(file_obj.name)
        NewfilePath = os.path.join(tmpdir, FileName)
        if file_obj.name.endswith(".csv"):
            titles = pd.read_csv(NewfilePath)["title"]
            outputPath = os.path.join(tmpdir, "ref.bib")
            with open(outputPath, 'wb') as w:
                for title in titles:
                    bib = get_one_bib(title)
                    if bib:
                        w.write(bib.encode())
            return outputPath


def chat_bot(message, history, prompt):
    speaker = SparkGPT(prompt)
    answer = speaker.ask(message, flow_print=True)
    for i in range(len(answer)):
        yield answer[:i + 1]


def chatsum_stream(pf, history, prompt=None):
    txt = PDFReader(pf.value).forward(abstract_only=True)
    for res in chatglm_stream(txt, history, prompt):
        yield res


def chatglm_stream(txt, history, prompt=None):
    if not prompt:
        prompt = "{}"
    res = requests.post(CHATGLM_ADDRESS + "stream", json={"query": prompt.format(txt), "history": history}, stream=True)
    temp_sec = []
    for byte_line in res:
        txt = byte_line.decode(errors='ignore')
        temp_sec.append(txt)
        if re.findall(r"\"finished\": (.*?)}", "".join(temp_sec)):
            res = json.loads("".join(temp_sec))["delta"]
            if res == "[EOS]":
                break
            history[-1][1] += json.loads("".join(temp_sec))["delta"]
            temp_sec = []
            yield history