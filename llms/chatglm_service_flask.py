#! /usr/bin/python3
from gevent import monkey, pywsgi

monkey.patch_all()
from flask import Flask, request, Response
import torch
from transformers import AutoTokenizer, AutoModel
import argparse
import logging
import os
import json
import sys


def getLogger(name, file_name, use_formatter=True):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s    %(message)s')
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    if file_name:
        handler = logging.FileHandler(file_name, encoding='utf8')
        handler.setLevel(logging.INFO)
        if use_formatter:
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


logger = getLogger('ChatGLM', 'chatlog.log')

MAX_HISTORY = 5


class ChatGLM():
    def __init__(self, CKPTS, quantize_level, gpu_id) -> None:
        logger.info("Start initialize model...")
        self.tokenizer = AutoTokenizer.from_pretrained(CKPTS, trust_remote_code=True)
        self.model = self._model(CKPTS, quantize_level, gpu_id)
        self.model.eval()
        _, _ = self.model.chat(self.tokenizer, "你好", history=[])
        logger.info("Model initialization finished.")

    def _model(self, CKPTS, quantize_level, gpu_id):
        quantize = int(quantize_level)
        if gpu_id == '-1':
            if quantize == 8:
                print('CPU模式下量化等级只能是16或4，使用4')
                CKPTS = "THUDM/chatglm-6b-int4"
            elif quantize == 4:
                CKPTS = "THUDM/chatglm-6b-int4"
            model = AutoModel.from_pretrained(CKPTS, trust_remote_code=True).float()
        else:
            gpu_ids = gpu_id.split(",")
            self.devices = ["cuda:{}".format(id) for id in gpu_ids]
            if quantize == 16:
                model = AutoModel.from_pretrained(CKPTS, trust_remote_code=True).half().cuda()
            else:
                model = AutoModel.from_pretrained(CKPTS, trust_remote_code=True).half().quantize(quantize).cuda()
        return model

    def clear(self) -> None:
        if torch.cuda.is_available():
            for device in self.devices:
                with torch.cuda.device(int(device)):
                    torch.cuda.empty_cache()
                    torch.cuda.ipc_collect()

    def answer(self, query: str, history):
        response, history = self.model.chat(self.tokenizer, query, history=history)
        history = [list(h) for h in history]
        return response, history

    def stream(self, query, history):
        if query is None or history is None:
            yield {"query": "", "response": "", "history": [], "finished": True}
        size = 0
        response = ""
        for response, history in self.model.stream_chat(self.tokenizer, query, history):
            this_response = response[size:]
            history = [list(h) for h in history]
            size = len(response)
            yield {"delta": this_response, "response": response, "finished": False}
        logger.info("Answer - {}".format(response))
        yield {"query": query, "delta": "[EOS]", "response": response, "history": history, "finished": True}


def start_server(CKPTS, quantize_level, http_address: str, port: int, gpu_id: str):
    os.environ['CUDA_DEVICE_ORDER'] = 'PCI_BUS_ID'
    os.environ['CUDA_VISIBLE_DEVICES'] = gpu_id
    bot = ChatGLM(CKPTS, quantize_level, gpu_id)
    app = Flask(__name__)

    @app.route("/")
    def index():
        return Response(json.dumps({'message': 'started', 'success': True}, ensure_ascii=False),
                        content_type="application/json")

    @app.route("/chat", methods=["GET", "POST"])
    def answer_question():
        result = {"query": "", "response": "", "success": False}
        try:
            if "application/json" in request.content_type:
                arg_dict = request.get_json()
                text = arg_dict["query"]
                ori_history = arg_dict["history"]
                logger.info("Query - {}".format(text))
                if len(ori_history) > 0:
                    logger.info("History - {}".format(ori_history))
                history = ori_history[-MAX_HISTORY:]
                history = [tuple(h) for h in history]
                response, history = bot.answer(text, history)
                logger.info("Answer - {}".format(response))
                ori_history.append((text, response))
                result = {"query": text, "response": response,
                          "history": ori_history, "success": True}
        except Exception as e:
            logger.error(f"error: {e}")
        return Response(json.dumps(result, ensure_ascii=False), content_type="application/json")

    @app.route("/stream", methods=["POST"])
    def answer_question_stream():
        def decorate(generator):
            for item in generator:
                yield json.dumps(item, ensure_ascii=False)

        text, history = None, None
        try:
            if "application/json" in request.content_type:
                arg_dict = request.get_json()
                text = arg_dict["query"]
                ori_history = arg_dict["history"]
                logger.info("Query - {}".format(text))
                if len(ori_history) > 0:
                    logger.info("History - {}".format(ori_history))
                history = ori_history[-MAX_HISTORY:]
                history = [tuple(h) for h in history]
        except Exception as e:
            logger.error(f"error: {e}")
        return Response(decorate(bot.stream(text, history)), mimetype='text/event-stream')

    @app.route("/clear", methods=["GET", "POST"])
    def clear():
        history = []
        try:
            bot.clear()
            return Response(json.dumps({"success": True}, ensure_ascii=False), content_type="application/json")
        except Exception as e:
            return Response(json.dumps({"success": False}, ensure_ascii=False), content_type="application/json")

    @app.route("/score", methods=["GET"])
    def score_answer():
        score = request.get("score")
        logger.info("score: {}".format(score))
        return {'success': True}

    logger.info("starting server...")
    server = pywsgi.WSGIServer((http_address, port), app)
    server.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Stream API Service for ChatGLM-6B')
    parser.add_argument('--ckpts', '-c', help='Model path', default="./ckpts/chatglm2-6b")
    parser.add_argument('--device', '-d', help='device，-1 means cpu, other means gpu ids', default='2')
    parser.add_argument('--quantize', '-q', help='level of quantize, option：16, 8 or 4', default=16)
    parser.add_argument('--host', '-H', help='host to listen', default='0.0.0.0')
    parser.add_argument('--port', '-P', help='port of this service', default=8800)
    args = parser.parse_args()
    start_server(args.ckpts, args.quantize, args.host, int(args.port), args.device)
