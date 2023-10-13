# -*- coding: utf-8 -*-
"""
Author  : Hanlei Jin
Date    : 2023/5/27
E-mail  : jin@smail.swufe.edu.cn
"""
import re
import copy
import fitz


class PDFReader:
    def __init__(self, fp, REMOVE_FSIZE_PERCENT=0.9, REMOVE_APPENDIX=True, STOP_WORDS="arxiv:|researchgate.net"):
        """
            fp: pdf文件路径
            REMOVE_FSIZE_PERCENT: 去除小于正文字体的字，设置为0则不去除
            REMOVE_APPENDIX: 去除reference之后的章节
            STOP_WORDS: 删除带有此字符的行，用|隔开
        """
        self.itxt = 0  # Index 0 文本
        self.ifont = 1  # Index 1 字体大小
        self.ibbox = 2  # Index 2 文本框大小
        self.REMOVE_FSIZE_PERCENT = REMOVE_FSIZE_PERCENT
        self.REMOVE_APPENDIX = REMOVE_APPENDIX
        self.REMOVE_PATTERN = re.compile(STOP_WORDS, re.I)
        self.fp = fp

    def read_lines(self, fp):
        """
            获得pdf的每一行
            return: (每一行包括[文本,字体,位置和大小,元数据], 正文字体大小)
        """
        with fitz.open(fp) as doc:
            meta_line = []
            fsize_all = {}
            for page in doc:
                # 去除页码
                if meta_line and meta_line[-1][self.itxt].isdigit():
                    meta_line.pop(-1)
                text_areas = page.get_text("dict")
                for block in text_areas["blocks"]:
                    if "lines" in block:
                        for line in block["lines"]:
                            txt = "".join([i["text"] for i in line["spans"]])
                            if len(txt) == 0:
                                continue
                            font_size = {}
                            for span in line["spans"]:
                                font_size[span["size"]] = fsize_all.setdefault(span["size"], 0) + len(span["text"])
                                fsize_all[span["size"]] = font_size.setdefault(span["size"], 0) + len(span["text"])
                            pf = max(font_size, key=font_size.get)
                            meta_line.append([txt, pf, line["bbox"], line])
            # 主字体
            main_fsize = max(fsize_all, key=fsize_all.get)
        return meta_line, main_fsize

    def get_section(self, meta_line, main_fsize):
        """
            获得论文的每一章节
            return:每一章节的列表
        """
        fsize_threshold = main_fsize * self.REMOVE_FSIZE_PERCENT
        meta_sec = []
        sec = []
        # 去除停用词
        meta_line = [line for line in meta_line if not re.findall(self.REMOVE_PATTERN, line[self.itxt]) and
                     not line[self.ifont] <= fsize_threshold]
        for i, line in enumerate(meta_line):
            if i == 0:
                sec.append(line[self.itxt])
                continue
            if fsize_threshold and line[self.ifont] <= fsize_threshold:
                continue
            if line[self.itxt] == "Abstract":
                meta_sec.append(copy.deepcopy(sec))
                sec = ["\n# " + line[self.itxt]]
                continue
            if line[self.ibbox][0] > meta_line[i - 1][self.ibbox][0] * 1.5:
                continue
            # 上下两段字体相差小，即正文段落
            fsize_gap = (line[self.ifont] - meta_line[i - 1][self.ifont]) / max(line[self.ifont], meta_line[i - 1][self.ifont])
            if abs(fsize_gap) < 0.02:
                # 长单词换行时会以-分割，故去掉每行末尾的-并与下一行衔接
                if meta_line[i - 1][self.itxt].endswith("-"):
                    sec[-1] = sec[-1][:-1]
                else:
                    sec[-1] += " "
                sec[-1] += line[self.itxt]
                # bbox: ((左上角坐标)，(右下角坐标))
                # 不同段落，或图表标题
                if line[self.itxt].endswith(".") and \
                        (meta_line[i - 1][self.itxt] != "NEW_BLOCK") and \
                        (line[self.ibbox][2] - line[self.ibbox][0]) < (
                        meta_line[i - 1][self.ibbox][2] - meta_line[i - 1][self.ibbox][0]) * 0.7:
                    sec[-1] += "\n"
            else:
                # 单行且字体大且比上一行大，视作标题，加入#前缀
                if (i + 1 < len(meta_line)) and meta_line[i][self.ifont] > main_fsize and fsize_gap > 0:
                    meta_sec.append(copy.deepcopy(sec))
                    sec = ["\n# " + line[self.itxt]]
                else:
                    sec.append("\n" + line[self.itxt])
        meta_sec.append(copy.deepcopy(sec))
        return meta_sec

    def get_text(self, meta_sec):
        """
            合并每章节为文本
        """
        meta_txt = []
        for ms in meta_sec:
            final = " ".join(ms)
            meta_txt.append(final)
            if self.REMOVE_APPENDIX and ms[0].lower() == "\n# references":
                break
        meta_txt = self.merge_lower(meta_txt)
        meta_txt = self.clear_few_sec(meta_txt)
        meta_txt = '\n'.join(meta_txt).strip()
        meta_txt = re.sub(r'\s\n', '\n', meta_txt)
        meta_txt = re.sub(r'\n+', '\n', meta_txt)
        return meta_txt

    def clear_few_sec(self, meta_txt):
        """
            清除字数较少的章节
        """
        for index, block_txt in enumerate(meta_txt):
            if len(block_txt) < 100:
                meta_txt[index] = ''
        return meta_txt

    def merge_lower(self, meta_txt):
        """
            合并小写开头的段落块
        """
        for _ in range(10):
            for index, block_txt in enumerate(meta_txt):
                if index == 0:
                    continue
                if not re.match(r"^[a-z]+", block_txt):
                    if meta_txt[index - 1] != '\n':
                        meta_txt[index - 1] += ' '
                    else:
                        meta_txt[index - 1] = ''
                    meta_txt[index - 1] += meta_txt[index]
                    meta_txt[index] = '\n'
        return meta_txt

    def forward(self, abstract_only=False):
        meta_line, main_fsize = self.read_lines(self.fp)
        meta_sec = self.get_section(meta_line, main_fsize)
        if abstract_only:
            for sec in meta_sec:
                if sec[0] == "\n# Abstract":
                    meta_sec = [sec]
        meta_txt = self.get_text(meta_sec)
        return meta_txt


if __name__ == '__main__':
    fp = "./pdfs/attention.pdf"
    pr = PDFReader(fp)
    txt = pr.forward(abstract_only=True)
    print(txt)