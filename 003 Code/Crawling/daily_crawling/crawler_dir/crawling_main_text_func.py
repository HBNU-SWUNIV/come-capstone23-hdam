# 커스텀 함수
from crawler_dir.trimming_dir import trimming_func as tf
# 라이브러리 import
import time

# sleep_sec은 0.7초로 설정
sleep_sec = 0.7

def crawling_main_text(soup, press):
    needless = []

    title = soup.head.title.text
    content = soup.find("article", {'id': 'dic_area'})
    if content == None:
        content = "a"
    thumbnail = soup.find('article', {'id' : 'img1'})
    if thumbnail == None:
        thumbnail = 'a'

    # 필요없는 사진, 요약 설명
    pho_exps = soup.select("#dic_area > span")
    summary_exps = soup.select("#dic_area > strong")
    if len(summary_exps) == 0:
        summary_exps = soup.select("#dic_area > ul > li")
    others_exps = ""

    if press == "머니S":
        pho_exps = soup.select("#dic_area > table")
    elif press == "머니투데이":
        others_exps = soup.select("#dic_area > b")
        pho_exps = soup.select("#dic_area > span")
    elif press == "이데일리":
        pho_exps = soup.select("#dic_area > table")
        others_exps = soup.select("#dic_area > div.pharm")
        if len(pho_exps) == 0:  # 이데일리 아주 가끔나오는 변종
            pho_exps = soup.select("#dic_area > figure")

    needless = tf.needless_explain(pho_exps, summary_exps, others_exps)
    if content == "a":
        content = "a"
    else:
        content = tf.del_pho_exp(needless, content.text)

    # 뉴스 기사 다듬기 및 전처리 함수 호출
    content = tf.trimming_text(press, content)
    time.sleep(sleep_sec)

    return title, content, thumbnail
