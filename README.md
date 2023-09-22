# ChatScholar
ChatScholar，一站式论文检索和生成平台。

## 关键技术点
- 爬虫：基于requests和beautifulsoup，利用代理ip池爬取[DBLP](https://dblp.uni-trier.de/)论文信息，实现了增量更新（如果要爬的url已经存在数据库，则不爬）；
- 数据库：Mysql存期刊会议和用户信息，MongoDB储存爬取的论文；
- 后端接口：Flask调度算法；
- LLM接口：暂时使用[讯飞星火](https://xinghuo.xfyun.cn/)；
- 前端页面：Gradio（比较简陋，但是功能基本都能实现）。

## 项目简介

项目包含以下功能：

1. 论文检索：能够通过选择期刊会议（目前包含所有CCF推荐期刊会议论文）+时间+关键词，即时返回相关论文和数量统计，并且提供结果表格下载。此外，还提供期刊会议推荐、保存用户常用期刊会议等。不用再“一个个期刊，一场场会议，一期又一期的重复性关键词查找”；

2. bib生成：批量输入论文标题，输出bib文件；

3. 论文总结生成：正在合理化设计中，这个模块目标是在检索结果/输入标题后，输出n篇论文的总结。以及上传论文pdf后，采用问答形式对论文进行解读。

## 项目结构

```shell
ChatScholar
├── settings.py
├── DB_runer.py
├── api.py
├── app.py
├── app_utils
│   ├── app_request.py
│   ├── config.json
│   └── xunfei_request.py
├── db_utils
│   ├── crawler
│   │   ├── crawl_utils.py
│   │   ├── get_dblp.py
│   ├── mongo_utils.py
│   ├── mysql_utils.py
├── README.md
├── requirements.txt
├── temp
```

## Run

安装依赖：

```shell
pip install -r requirements.txt
```

修改settings文件后，运行爬虫和构建数据库：

```shell
python DB_runer.py
```

运行后端算法接口：

```shell
python api.py
```

运行前端页面：

```shell
gradio app.py
```

## 鸣谢

本项目参考了以下Repo：

- [dblp-api](https://github.com/alumik/dblp-api)

- [CCF-Rec-Paper-DB](https://github.com/tmylla/CCF-Rec-Paper-DB)
- [xfyun-spark-api](https://github.com/zibuyu2015831/xfyun-spark-api)

## TODO

- [ ] 部分论文缺失，原因是一些期刊/会议的格式混乱，例如会议论文集发在某期刊上，需要设计爬虫和数据格式；
- [ ] 部分期刊会议会增量更新论文，当前的url中的论文不完整，需要设计最近页面的更新爬虫；
- [ ] 论文pdf读取和解析，预备参考[gpt_academic](https://github.com/binary-husky/chatgpt_academic)和[ChatPaper](https://github.com/kaixindelele/ChatPaper)；
- [ ] 论文LLM训练；
- [ ] 用户能储存固定的期刊会议集，以便下次快速查找；
- [ ] 更美观实用的前端；
- [ ] 其他论文统计类的功能。