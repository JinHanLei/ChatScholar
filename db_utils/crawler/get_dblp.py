# -*- coding: utf-8 -*-
"""
Author  : Hanlei Jin
Date    : 2023/8/2
E-mail  : jin@smail.swufe.edu.cn
"""
import re
from random import randint
import requests
from bs4 import BeautifulSoup
from tqdm.auto import tqdm
from requests.adapters import HTTPAdapter
from settings import PROXIES

def get_url(url):
    """
        访问url，返回网页内容
    """
    USER_AGENTS = [
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
        "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
        "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
        "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
        "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
        "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
        "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
        "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
    ]
    random_agent = USER_AGENTS[randint(0, len(USER_AGENTS) - 1)]
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'user-agent': random_agent,
    }
    s = requests.Session()
    s.mount('http://', HTTPAdapter(max_retries=3))
    s.mount('https://', HTTPAdapter(max_retries=3))
    if PROXIES:
        proxies = PROXIES
        r = s.get(url, headers=headers, proxies=proxies, timeout=60)
    else:
        r = s.get(url, headers=headers, timeout=60)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    soup = BeautifulSoup(r.text, 'html.parser')
    return soup


def get_conf(conf_mian_url, already_url):
    """
        获得会议主页的信息，包括会议年份、备注、链接等，
        案例见：https://dblp.uni-trier.de/db/conf/aaai/。特例如下：
        1.统一说明近几年的论文发表在某期刊上，见‘https://dblp.uni-trier.de/db/conf/fse/’，
        2.每年的会议分别说明发表在期刊的某期，见‘https://dblp.uni-trier.de/db/conf/ches/’
    """
    soup = get_url(conf_mian_url)
    paper_db = []
    years = soup.find_all('h2', attrs={'id': re.compile('\d+')})
    # TODO: 情况1
    progress_bar = tqdm(range(len(years)))
    for year in years:
        year_str = year.attrs['id']
        # 这一年会议的若干会场，包括主会议和workshop等
        try:
            # 会议标题之下没有内容如：https://dblp.uni-trier.de/db/conf/cnhpca/;https://dblp.uni-trier.de/db/conf/usenix/
            venues = year.parent.next_sibling.find_all('li', attrs={'class': "entry editor toc"})
        except:
            continue
        for sub_info in venues:
            db_temp = {}
            db_temp['year'] = year_str
            db_temp['name'] = year.text

            db_temp['venue_name'] = sub_info.find('span', attrs={'class': 'title'}).text
            db_temp['venue_abbr'] = sub_info['id']
            try:
                every_url = sub_info.find('a', attrs={'class': 'toc-link'}, text='[contents]')['href']
                if url in already_url:
                    continue
                else:
                    db_temp["url"] = every_url
            except:
                print(f"未能获取{db_temp['venue_name']}的URL")
                continue
            db_temp['count'], db_temp['papers'] = get_papers(db_temp['url'])

            progress_bar.set_description('Conf: {} - Year: {}'.format(db_temp['name'], db_temp['year']))
            progress_bar.update(1)

            if db_temp:
                paper_db.append(db_temp)

    # TODO: 情况2
    # for p_soup in soup.find_all('p'):
    #     if 'Proccedings published in' in p_soup.text:
    #         pass
    return paper_db

def get_papers(venue_url):
    papers = []
    try:
        soup = get_url(venue_url)
        # 期刊一般是article，会议一般是inproceedings
        papers_info = soup.find_all('li',
                                    attrs={'class': ['entry inproceedings', 'entry incollection', 'entry article']})
        for paper_info in papers_info:
            papers.append(paper_info.find('span', attrs={'class': 'title'}).text)
        return len(papers), papers
    except:
        print(f"未能获取{venue_url}的内容")
        return 0, None


def get_bib(title):
    paper_url = "https://dblp.uni-trier.de/search/publ/inc?q={}&h=30&f=0&s=ydvspc".format(title)
    try:
        bib_url = get_url(paper_url).find('a', attrs={'rel': "nofollow"}).attrs['href']
        bib = get_url(bib_url).find('div', attrs={'id': "bibtex-section"}).text.strip()
        return bib
    except:
        return ""


def get_jour(jour_mian_url, already_url):
    """
        获得期刊主页的信息，包括期刊年份、卷号、链接等，
        volume有两种格式：
        1.[年份: Volumes xx * n]，其中xx是带href的卷号，如：https://dblp.uni-trier.de/db/journals/ai/
        2.[Volume xx, 年份]，一整个是href，如：https://dblp.uni-trier.de/db/journals/tois/
        特例如下：
        1.部分期刊中途改名，https://dblp.uni-trier.de/db/journals/tois/。
    """
    soup = get_url(jour_mian_url)
    paper_db = []
    year_pattern = re.compile('(19|20)[0-9].')
    # 匹配Volume格式2
    volume_pattern = re.compile('Volume (\d+)')
    sections = soup.find('div', attrs={'id': 'main'}).find_all('ul', recursive=False)
    for section in sections:
        years = section.find_all('li')
        progress_bar = tqdm(range(len(years)))
        for year in years:
            try:
                # li中不存在volume和链接，如：https://dblp.uni-trier.de/db/journals/jsa/
                year_str = re.search(year_pattern, year.text).group()
                volumes = year.find_all('a')
            except:
                continue
            for sub_info in volumes:
                db_temp = {}
                db_temp['year'] = year_str
                db_temp["volume"] = sub_info.text
                if "Volume" in sub_info.text:
                    db_temp["volume"] = re.findall(volume_pattern, sub_info.text)[0]
                if sub_info['href'] in already_url:
                    continue
                else:
                    db_temp["url"] = sub_info['href']
                    db_temp['count'], db_temp['papers'] = get_papers(db_temp['url'])
                    progress_bar.set_description('Year: {} - Venues: {}'.format(db_temp['year'], db_temp['volume']))
                    progress_bar.update(1)
                    if db_temp:
                        paper_db.append(db_temp)
    return paper_db


def get_publ(url, is_conf, flag=[]):
    return get_conf(url, flag) if is_conf else get_jour(url, flag)


if __name__ == '__main__':
    # url = "https://dblp.uni-trier.de/db/journals/tocs/"
    # url = "https://dblp.uni-trier.de/db/conf/aaai/"
    # url = "https://dblp.uni-trier.de/db/journals/ai/"
    # url = "https://dblp.uni-trier.de/db/conf/fse/"
    url = "https://dblp.uni-trier.de/db/conf/isca/index.html"
    res = get_conf(url, [])
    # res = get_jour(url, [])
    # res = get_bib("Transparency, Detection and Imitation in Strategic ")
    print(res)