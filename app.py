# -*- coding: utf-8 -*-
"""
Author  : Hanlei Jin
Date    : 2023/9/11
E-mail  : jin@smail.swufe.edu.cn
"""
import re

import gradio as gr
from app_utils.app_request import get_ccf, search_paper, get_one_bib, generate_bib_file, chatglm_stream, \
    chatsum_stream, generate_file, login

with gr.Blocks() as demo:
    with gr.Row():
        wel_txt = "# {}，欢迎使用ChatScholar"
        welcome = gr.Markdown(wel_txt.format("游客"))

    with gr.Tab("🔍️ 检索"):
        with gr.Row():
            with gr.Column():
                begin_year = gr.Slider(1999, 2023, value=2017, step=1, label="Begin", info="请选择起始年份")
                end_year = gr.Slider(1999, 2023, value=2023, step=1, label="End", info="请选择截止年份")
            with gr.Column():
                ccf = get_ccf()
                selected_publ = gr.Dropdown(ccf, multiselect=True, label="Publications", info="请选择期刊会议")
            with gr.Column():
                keywords = gr.Textbox(placeholder="请输入关键词，以分号;分割", label="Keywords")
                is_strict = gr.Checkbox(value=True, label="严格匹配（满足所有关键字）")
                search_btn = gr.Button("🔍搜索", variant="primary")
        publ_ex = gr.Examples(examples=[[["TKDE", "TOIS", "ACL", "SIGIR", "EMNLP", "AAAI", "IJCAI", "NeurIPS", "WWW"],
                                         "summarization"]], inputs=[selected_publ, keywords])
        len_res = gr.Markdown(value="")
        with gr.Accordion("下载区", open=False):
            download = gr.File(label="下载结果文件")
        paper_df = gr.HTML("")
        search_btn.click(search_paper, inputs=[begin_year, end_year, selected_publ, keywords, is_strict],
                         outputs=[paper_df, len_res, download])

    with gr.Tab("🤗 Chat"):
        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(label=f"当前模型：ChatGLM")
            with gr.Column(scale=1):
                with gr.Row():
                    txt = gr.Textbox(label="Input", value="", scale=2)
                    prompt = gr.Textbox(label="Prompt")
                with gr.Row():
                    submit_btn = gr.Button("Chat !", variant="primary")
                with gr.Row():
                    reset_btn = gr.Button("清除", variant="secondary")
                    stop_btn = gr.Button("停止", variant="secondary")
                with gr.Row(visible=False) as chat_pdf:
                    with gr.Accordion("点击展开“文件上传区”。", open=False):
                        upload_pdf = gr.Files(label="目前仅支持pdf")
                        pf = gr.State()
                        if keywords.value is None:
                            keywords.value = "Computer Science"
                        prompt_sum = gr.Textbox(label="Prompt",
                                                value="You are a researcher in the field of " + keywords.value +
                                                      " who is good at summarizing papers using concise statements. "
                                                      "Give the article: {} Summarize in one sentences. Summary:")
                        summarize_btn = gr.Button("总结", variant="primary")
                        upload_pdf.change(fn=generate_file, inputs=upload_pdf, outputs=pf)
                        summarize_btn.click(fn=lambda msg, his: (
                        msg, his + [["正在读取" + re.findall("/(.*?\.pdf)", str(msg.value))[0], ""]]),
                                            inputs=[pf, chatbot],
                                            outputs=[pf, chatbot],
                                            queue=False).then(chatsum_stream, [pf, chatbot, prompt_sum], chatbot)

        submit_btn.click(fn=lambda msg, his: ("", his + [[msg, ""]]),
                         inputs=[txt, chatbot],
                         outputs=[txt, chatbot],
                         queue=False).then(chatglm_stream, [txt, chatbot, prompt], chatbot)

    with gr.Tab("📜 引用"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("## 单个标题示例")
                title = gr.Textbox(label="Title")
                gr.Examples(examples=["Degradation Accordant Plug-and-Play for Low-Rank Tensor Completion."],
                            inputs=title)
                get_bib_btn = gr.Button("🔍获取", variant="primary")
                bib_output = gr.Textbox(label="bib_output")
                get_bib_btn.click(get_one_bib, inputs=[title], outputs=bib_output)
            with gr.Column(visible=False) as ref_file:
                gr.Markdown("## 文件操作")
                upload_csv = gr.File(label="上传csv文件，请将论文标题列命名为title")
                outputs_bib = gr.File(label="下载bib文件")
                upload_csv.change(fn=generate_bib_file, inputs=upload_csv, outputs=outputs_bib)

    with gr.Tab("🏆 登录"):
        session = gr.State({"state": False})

        with gr.Row():
            with gr.Column(scale=1, visible=True) as login_block:
                gr.Markdown("## 欢迎登录")
                uname = gr.Textbox(label="用户名", scale=1)
                pwd = gr.Textbox(label="密码", type="password")
                login_btn = gr.Button("登录", variant="primary")

            with gr.Column(scale=2):
                gr.Markdown("## 登录解锁更多功能")
                gr.Markdown("### TODO:")
                gr.Markdown("1. 检索：储存自定义的期刊会议列表；一键全选科研机构的分类（如CCF-A）；模糊匹配/全文检索\n"
                            "2. Chat：专业SciChat大模型；全文问答；多文档摘要（支持多pdf上传）\n"
                            "3. 引用：支持多种引用格式")

        vip_func = [chat_pdf, ref_file, login_block]

        def vip_mode(s):
            return [i.update(visible=not i.visible) for i in vip_func] if s.value["state"] else [i.update(visible=False) for i in vip_func]

        login_btn.click(lambda u, p: login(u, p), [uname, pwd], session) \
            .then(lambda s: wel_txt.format(s.value["uname"]), session, welcome) \
            .then(lambda s: gr.Info("用户名或者密码不正确") if not s.value["state"] else gr.Info("登录成功！"), session) \
            .then(lambda s: vip_mode(s), session, vip_func)

demo.queue().launch(share=True)
