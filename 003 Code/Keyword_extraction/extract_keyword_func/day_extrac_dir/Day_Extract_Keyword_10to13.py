# Import Library
import json
import boto3

import time  # time.sleep() for Crawling
from datetime import datetime  # Chect runtime

from PyKomoran import *  # 형태소 분석기
import numpy as np

# About Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By  # Search Element
from selenium.webdriver.chrome.service import Service  # Chrome 경로 설정
from selenium.webdriver.chrome.options import Options  # Selenium에 UserAgent, Headless Chrome

# GET MODULE
from day_extrac_dir.crawlingArticle import crawlingTitleAndContents
from day_extrac_dir.contentsToSentences import contentsToSentences
from day_extrac_dir.getNounsFromSentences import getNounsInSentences
from day_extrac_dir.getRanks import getRanks
from day_extrac_dir.keywords import keywords

from concurrent.futures import ThreadPoolExecutor, as_completed  # 멀티스레드드

# 전역 변수 선언

# 동적 크롤링을 위한 time.sleep()
sleep_sec = 0.3

# 컨텐츠를 담을 빈 Dictionary, 인덱스
news_dict = {}
news_index = 0

# 뉴스 개수를 세는 변수
newsCount = 0

# 키워드의 순위를 지정할 리스트
keyword_dict = dict()

# Komoran 형태소 분석기 사용자 사전 추가
komoran = Komoran(DEFAULT_MODEL['FULL'])

# 분석을 진행할 시간
analysis_time = ['10시간전', '11시간전', '12시간전', '13시간전']

# 반복문 탈출을 위한 flag 설정 (Flag는 전역변수로)
escape_flag = False
duplicated_flag = False


# 첫 시작 페이지 탐색
def CheckStartPage():
    ### 셀레니움 세팅
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1280x1696')
    chrome_options.add_argument('--user-data-dir=/tmp/user-data')
    chrome_options.add_argument('--hide-scrollbars')
    chrome_options.add_argument('--enable-logging')
    chrome_options.add_argument('--log-level=0')
    chrome_options.add_argument('--v=99')
    chrome_options.add_argument('--single-process')
    chrome_options.add_argument('--data-path=/tmp/data-path')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--homedir=/tmp')
    chrome_options.add_argument('--disk-cache-dir=/tmp/cache-dir')
    chrome_options.add_argument(
        'user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')

    chrome_options.binary_location = "/opt/python/bin/headless-chromium"
    driver = webdriver.Chrome('/opt/python/bin/chromedriver', chrome_options=chrome_options)
    ###

    start_page = 1
    while True:
        driver.get("https://news.naver.com/main/main.naver?mode=LSD&mid=shm&sid1=101#&date=%2000:00:00&page=" + str(
            start_page))
        time.sleep(1)

        # 페이지의 "마지막 뉴스기사"를 통해 어디서 시작해야하는지 확인
        time_elem = driver.find_element(By.XPATH, '//*[@id="section_body"]/ul[4]/li[5]/dl/dd/span[3]')
        time.sleep(1)

        article_time = time_elem.text
        split_article_time = article_time.split('시간전')  # 시간 전으로 분리
        # 시간전으로 분리가 되면서, 페이지의 마지막 뉴스기사가 4시간전 이상의 숫자가 나오면 그 페이지부터 분석 시작
        if split_article_time[0].isdigit() and int(split_article_time[0]) >= 10:
            break
        else:
            start_page += 1

    driver.quit()  # 드라이버 종료

    # 반복문 끝. "4시간전" 이상이 존재하는 시작 페이지부터 분석

    print("시작 페이지는 : ", start_page)
    return start_page


def CrawlingToMultiprocessing(param1, page):
    # 전역 변수 불러오기
    global sleep_sec
    global news_dict
    global news_index
    global newsCount
    global keyword_dict
    global komoran
    global escape_flag
    global duplicated_flag

    ### 셀레니움 세팅
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1280x1696')
    chrome_options.add_argument('--user-data-dir=/tmp/user-data')
    chrome_options.add_argument('--hide-scrollbars')
    chrome_options.add_argument('--enable-logging')
    chrome_options.add_argument('--log-level=0')
    chrome_options.add_argument('--v=99')
    chrome_options.add_argument('--single-process')
    chrome_options.add_argument('--data-path=/tmp/data-path')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--homedir=/tmp')
    chrome_options.add_argument('--disk-cache-dir=/tmp/cache-dir')
    chrome_options.add_argument(
        'user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')

    chrome_options.binary_location = "/opt/python/bin/headless-chromium"
    driver = webdriver.Chrome('/opt/python/bin/chromedriver', chrome_options=chrome_options)
    ###

    ### 크롤링 시작
    while True:
        driver.get("https://news.naver.com/main/main.naver?mode=LSD&mid=shm&sid1=101#&date=%2000:00:00&page=" + str(
            page))  # 경제뉴스 이동
        i = param1
        for j in range(1, 6):
            time.sleep(sleep_sec)
            time_elem = driver.find_element(By.XPATH, '//*[@id="section_body"]/ul[' + str(i) + ']/li[' + str(
                j) + ']/dl/dd/span[3]')

            article_time = time_elem.text

            split_article_time = article_time.split('시간전')  # 시간 전으로 분리

            if split_article_time[0].isdigit() and int(split_article_time[0]) >= 14:
                escape_flag = True
                break

            if article_time in analysis_time:
                try:  # 일반적인 경우(썸네일이 존재할때)
                    article_elem = driver.find_element(By.XPATH,
                                                       '//*[@id="section_body"]/ul[' + str(i) + ']/li[' + str(
                                                           j) + ']/dl/dt[2]/a')
                except:  # 썸네일 미존재시
                    article_elem = driver.find_element(By.XPATH,
                                                       '//*[@id="section_body"]/ul[' + str(i) + ']/li[' + str(
                                                           j) + ']/dl/dt/a')

                time.sleep(sleep_sec)

                url = article_elem.get_attribute('href')  # select한 기사의 네이버 제휴 url 추출
                time.sleep(sleep_sec)

                title, contents = crawlingTitleAndContents(url)  # crawlingArticle.py, 제목 및 본문 크롤링

                ### 아예 같은 제목이 존재하는 경우에는 크롤링을 하지 않도록 코드작성
                for duplicated_index in range(news_index):
                    if news_dict[duplicated_index]['title'] == title:
                        duplicated_flag = True

                if duplicated_flag:
                    duplicated_flag = False
                    continue
                ###

                # 제목과 본문을 합친 것을 리스트 형태로
                news_content = title + contents
                sentence = contentsToSentences(news_content)  # 하나의 기사 전체를 문장으로 나누어 리스트로 저장장
                nouns = getNounsInSentences(komoran, sentence)  # 토큰화화

                ### words_graph, idx2word = buildWordsGraph(nouns) 이 코드를 다른 람다함수에 옮겨서 사용(라이브러리 크기 때문에)

                # 호출할 Lambda 함수의 ARN 지정
                target_function_arn = 'arn:aws:lambda:ap-northeast-2:093169469773:function:day_keyword_func'

                # 호출할 함수의 입력 데이터
                input_data = {
                    'nouns': nouns,
                    'words_graph': 'value1',
                    'idx2word': 'value2'
                }

                # AWS Lambda 클라이언트 생성
                lambda_client = boto3.client('lambda')

                # 다른 Lambda 함수를 호출
                response = lambda_client.invoke(
                    FunctionName=target_function_arn,
                    InvocationType='RequestResponse',  # 동기 호출
                    Payload=json.dumps(input_data)  # 입력 데이터를 JSON 문자열로 변환
                )

                # 호출된 Lambda 함수의 응답 처리
                response_payload = json.loads(response['Payload'].read())

                # 리스트를 다시 NumPy 배열로 변환
                words_graph = response_payload['words_graph']  # json형태로 가져와야 해서 list로 저장되어 있음
                words_graph = np.array(words_graph)
                idx2word = response_payload['idx2word']
                ###

                word_rank_idx = getRanks(words_graph)
                sorted_word_rank_idx = sorted(word_rank_idx, key=lambda k: word_rank_idx[k], reverse=True)
                keyword_list = keywords(sorted_word_rank_idx, idx2word)
                newsCount += 1

                # 키워드 순위 측정
                for keyword in keyword_list:
                    if keyword in keyword_dict:
                        keyword_dict[keyword] += 1
                    else:
                        keyword_dict[keyword] = 1

                news_dict[news_index] = {'title': title,
                                         'content': contents,
                                         'keyword': keyword_list}

                news_index += 1
            else:
                pass

        if escape_flag:
            break;
        page += 1

    time.sleep(1)
    driver.quit()
    time.sleep(1)

    return param1


def DayKeywordCrawler_10to13():
    global keyword_dict
    global newsCount

    # 시작 페이지를 찾는 작업 실시
    start_page = CheckStartPage()

    ###### 멀티스레드 사용
    with ThreadPoolExecutor(max_workers=8) as executor:
        res = [executor.submit(CrawlingToMultiprocessing, i, start_page) for i in range(1, 5)]
        ######

        for future in as_completed(res):
            res_ = future.result()

    # 키워드 빈도 수를 기준으로 내림차순 정렬
    sorted_data = sorted(keyword_dict.items(), key=lambda x: x[1], reverse=True)

    # 데이터 뽑기 뽑기
    keyword_data = list()

    #  키워드 데이터를 [["부동산" 31],...] 이런 형태로 append
    for item in sorted_data:
        keyword_data.append([item[0], item[1]])

    return keyword_data, newsCount

