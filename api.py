# -*- coding: utf-8 -*-
"""
Author  : Hanlei Jin
Date    : 2023/9/12
E-mail  : jin@smail.swufe.edu.cn
"""
import json
import flask
from db_utils.crawler.get_dblp import get_bib
from db_utils.mongo_utils import MongoHandler

app = flask.Flask(__name__)


@app.route("/")
def homepage():
    return "Welcome to the ChatScholar API!"


@app.route("/ccf")
def get_ccf():
    res = {
        "code": 200
    }
    try:
        res.update({"res": MongoHandler().publs})
    except:
        res.update({"code": 488, "res": "Algorithm error."})
    return flask.jsonify(res)


@app.route("/search", methods=["POST", "GET"])
def search_papers():
    res = {
        "code": 200
    }
    try:
        if flask.request.method == "POST":
            data = flask.request.data.decode('utf-8')
            data = json.loads(data)
            res.update({"res": MongoHandler().search_paper(**data)})
    except:
        res.update({"code": 488, "res": ["Algorithm error."]})
    return flask.jsonify(res)


@app.route("/bib", methods=["POST", "GET"])
def get_bib_api():
    res = {
        "code": 200
    }
    try:
        if flask.request.method == "POST":
            data = flask.request.data.decode('utf-8')
            data = json.loads(data)
            res.update({"res": get_bib(data["title"]) + "\n\n"})
    except:
        res.update({"code": 488, "res": ["Algorithm error."]})
    return flask.jsonify(res)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8002, debug=True)
