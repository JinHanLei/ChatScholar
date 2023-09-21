# -*- coding: utf-8 -*-
"""
Author  : Hanlei Jin
Date    : 2023/9/11
E-mail  : jin@smail.swufe.edu.cn
"""
import gradio as gr
from app_utils.app_request import get_ccf, search_paper, get_one_bib, chat_bot, generate_file

session = gr.State({"uname": "游客"})

with gr.Blocks(title="ChatScholar") as demo:
    gr.Markdown("# {}，欢迎使用ChatScholar".format(session.value["uname"]))

    with gr.Tab("🔍️ 关键词检索"):
        with gr.Row():
            with gr.Column():
                begin_year = gr.Slider(1999, 2023, value=2017, step=1, label="Begin", info="请选择起始年份")
                end_year = gr.Slider(1999, 2023, value=2023, step=1, label="End", info="请选择截止年份")
            with gr.Column():
                # selected_level = gr.CheckboxGroup(choices=["只看CCF-A", "也看CCF-B", "还看CCF-C"], value=False, label="选择等级")
                ccf = get_ccf()
                selected_publ = gr.Dropdown(ccf, multiselect=True, label="Publications", info="请选择期刊会议")

            with gr.Column():
                keywords = gr.Textbox(placeholder="请输入关键词，以分号;分割", label="Keywords")
                is_strict = gr.Checkbox(value=True, label="严格匹配（满足所有关键字）")
                search_btn = gr.Button("🔍搜索")
        gr.Examples(examples=[[["TKDE", "TOIS", "ACL", "SIGIR", "EMNLP", "AAAI", "IJCAI", "NeurIPS", "WWW"],
                               "summarization"]], inputs=[selected_publ, keywords])
        len_res = gr.Markdown(value="")
        paper_df = gr.HTML("")
        download = gr.File(label="下载结果文件")
        search_btn.click(search_paper, inputs=[begin_year, end_year, selected_publ, keywords, is_strict],
                         outputs=[paper_df, len_res, download])

    with gr.Tab("📜 获取bib"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("## 单个标题示例")
                title = gr.Textbox(placeholder="请输入论文标题", label="paper_title")
                gr.Examples(examples=["Degradation Accordant Plug-and-Play for Low-Rank Tensor Completion."], inputs=title)
                get_bib_btn = gr.Button("🔍获取")
                bib_output = gr.Textbox(label="bib_output")
                get_bib_btn.click(get_one_bib, inputs=[title], outputs=bib_output)
            with gr.Column():
                gr.Markdown("## 文件操作")
                upload_csv = gr.File(label="上传csv文件，请将论文标题列命名为title")
                outputs_bib = gr.File(label="下载bib文件")
                upload_csv.change(fn=generate_file, inputs=upload_csv, outputs=outputs_bib)

    with gr.Tab("🤗 Chat"):
        prompt = gr.Textbox("You are a researcher who is good at summarizing papers using concise statements.")
        gr.ChatInterface(chat_bot,
                         additional_inputs=prompt,
                         submit_btn="发送",
                         retry_btn="重新生成回复",
                         undo_btn="撤回",
                         theme="soft",
                         clear_btn="清除")


def login(name, pwd):
    if name == "1" and pwd == "1":
        return True


# demo.queue().launch(auth=login, auth_message="欢迎使用ChatScholar")
demo.queue().launch(share=True)
