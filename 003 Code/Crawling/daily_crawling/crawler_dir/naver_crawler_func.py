# 셀레니움 라이브러리
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# 셀레니움 속도 개선
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed  # 멀티스레드드

# 커스텀 함수 import
import crawler_dir.is_valid_article_func as ivaf
import crawler_dir.crawling_main_text_func as cmtf

# 데베
import boto3
from boto3.dynamodb.conditions import Key, Attr  # 테이블 읽기기

# sleep_sec은 0.2초로 설정
sleep_sec = 0.2

pressList1 = ["머니투데이", "데일리안", "헤럴드경제", "이데일리", "YTN", "서울경제", "뉴스1", "경향신문", "파이낸셜뉴스", "머니S"]
pressList2 = ['매일경제', '뉴시스', '연합뉴스', '한국경제', 'KBS', '중앙일보', '조선일보', '국민일보', '아시아경제', '조선비즈']


def crawling_func(keyword, newsCount, pressList):
    ###
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

    # 딕셔너리 형식으로 뉴스 저장장
    news_dict = {}
    dict_idx = 0  # 뉴스갯수

    # 크롤링 시작
    news_url = 'https://search.naver.com/search.naver?where=news&query={}'.format(keyword)
    driver.get(news_url)
    time.sleep(sleep_sec)

    #### 옵션 클릭
    search_opn_btn = driver.find_element(By.XPATH, '//a[@class="btn_option _search_option_open_btn"]')
    search_opn_btn.click()
    time.sleep(sleep_sec)

    #### 기간(순서 중요, 기간, 언론사 등 선택 후 -> 정렬 선택)
    bx_term = driver.find_element(By.XPATH,
                                  '//div[@role="listbox" and @class="mod_group_option_sort _search_option_detail_wrap"]//li[@class="bx term"]')

    # 1일까지
    term_tablist = bx_term.find_elements(By.XPATH, './/div[@role="tablist" and @class="option"]/a')

    driver.implicitly_wait(20)  # 유독 여기에서 오류가 남

    term_tablist[3].click()
    time.sleep(sleep_sec)

    #### 정렬
    bx_lineup = driver.find_element(By.XPATH,
                                    '//div[@role="listbox" and @class="mod_group_option_sort _search_option_detail_wrap"]//li[@class="bx lineup"]')

    # 정확성순
    lineup_tablist = bx_lineup.find_elements(By.XPATH, './/div[@role="tablist" and @class="option"]/a')
    lineup_tablist[1].click()
    time.sleep(sleep_sec)

    #### 언론사별 크롤링 시작
    for press in pressList1:  # 전체 진행수
        # ---------------------------------------------------------------------------------------------------- #

        no_exist = 0  # 검색결과가 없는 경우
        all_search = 0  # 모든 뉴스를 다 돌아봐도 내가 입력한 값보다 부족할 경우
        id = 1

        #### 언론사
        bx_press = driver.find_element(By.XPATH,
                                       '//div[@role="listbox" and @class="mod_group_option_sort _search_option_detail_wrap"]//li[@class="bx press"]')

        # 기준 두번 째(언론사 분류순) 클릭하고 오픈하기
        press_tablist = bx_press.find_elements(By.XPATH, './/div[@role="tablist" and @class="option"]/a')
        press_tablist[2].click()
        # time.sleep(sleep_sec)

        # 첫 번째 것(언론사 분류선택)
        bx_group = bx_press.find_elements(By.XPATH,
                                          './/div[@class="mod_select_option type_group _category_select_layer"]/div[@class="select_wrap _root"]')[
            0]

        # 언론사 분류
        press_kind_bx = bx_group.find_elements(By.XPATH, './/div[@class="group_select _list_root"]')[0]

        # 언론사 종류
        press_kind_btn_list = press_kind_bx.find_elements(By.XPATH,
                                                          './/ul[@role="tablist" and @class="lst_item _ul"]/li/a')
        time.sleep(sleep_sec)

        # -----언론사의 XPATH를 찾는 반복문-----
        for press_kind_btn in press_kind_btn_list:
            # time.sleep(30)

            # 언론사 종류를 순차적으로 클릭(좌측)

            press_kind_btn.click()
            time.sleep(sleep_sec)

            # 언론사선택(우측)
            press_slct_bx = bx_group.find_elements(By.XPATH, './/div[@class="group_select _list_root"]')[1]
            # 언론사 선택할 수 있는 클릭 버튼
            press_slct_btn_list = press_slct_bx.find_elements(By.XPATH,
                                                              './/ul[@role="tablist" and @class="lst_item _ul"]/li/a')
            # 언론사 이름들 추출
            press_slct_btn_list_nm = [psl.text for psl in press_slct_btn_list]
            # 언론사 이름 : 언론사 클릭 버튼 인 딕셔너리 생성 list_nm => 언론사 이름 btn_list => 언론사 클릭버튼
            press_slct_btn_dict = dict(zip(press_slct_btn_list_nm, press_slct_btn_list))

            # 원하는 언론사가 해당 이름 안에 있는 경우
            # 1) 클릭하고
            # 2) 더이상 언론사분류선택 탐색 중지
            if press in press_slct_btn_dict.keys():
                print('<{}> 카테고리에서 <{}>를 찾았으므로 언론사 탐색을 종료합니다'.format(press_kind_btn.text, press))
                press_slct_btn_dict[press].click()
                time.sleep(sleep_sec)
                break

            time.sleep(sleep_sec)

        #         #pressList에 있는 언론사를 찾았다면, 키워드에 대해 크롤링 시작
        #         print('\n=> <' + press + '> 에서 <' + keyword + '>에 대해 크롤링을 시작합니다.')

        #####동적 제어로 페이지 넘어가며 크롤링
        idx = 0
        cur_page = 1

        # newsCount를 담기위한 임시변수
        org_news_num = newsCount

        while idx < newsCount:
            # NewsList가 존재할때 try, 존재하지 않는다면 Except
            try:
                table = driver.find_element(By.XPATH, '//ul[@class="list_news"]')
            except:
                print("검색 결과가 존재하지 않습니다. 다음 언론사에서 검색합니다.")
                no_exist = 1
                break

            # '네이버 뉴스'의 태그를 찾는 과정
            li_list = table.find_elements(By.XPATH, './li[contains(@id, "sp_nws")]')
            area_list = [li.find_element(By.XPATH, './/div[@class="news_area"]') for li in li_list]
            info_list = [info.find_element(By.XPATH, './/div[@class="news_info"]') for info in area_list]
            group_list = [group.find_element(By.XPATH, './/div[@class="info_group"]') for group in info_list]
            a_list = [naver.find_element(By.XPATH, './/a[@class="info"][1]') for naver in group_list]
            time.sleep(sleep_sec)

            for n in a_list[:len(a_list)]:
                if idx == newsCount:
                    break

                n_url = n.get_attribute('href')

                isValid, soup = ivaf.is_valid_article(n_url)
                if isValid == True:
                    title, content, thumbnail = cmtf.crawling_main_text(soup, press)

                    # 문장이 비어있거나(이럴경우 'a' 출력) 같은 뉴스가 두번 저장될 경우
                    if content == 'a' or thumbnail == 'a' and dict_idx - 1 >= 0 and content == news_dict[dict_idx - 1][
                        'content']:
                        idx += 1
                        newsCount += 1
                        continue
                    news_dict[dict_idx] = {'title': title,
                                           'keyword': keyword,
                                           'agency': press,
                                           'url': n_url,
                                           'thumbnail': thumbnail,
                                           'content': content}
                    idx += 1
                    dict_idx += 1

                elif isValid == False:
                    idx += 1
                    newsCount += 1
                    continue

            # 아직 탐색을 끝마치지 못했을때,
            if idx < newsCount:
                cur_page += 1
                pages = driver.find_element(By.XPATH, '//div[@class="sc_page_inner"]')

                try:
                    next_page_url = [p for p in pages.find_elements(By.XPATH, './/a') if p.text == str(cur_page)][
                        0].get_attribute('href')
                # 원하는 양을 찾지 못하고 모든 뉴스기사를 다 돌아 봤을 경우
                except:
                    all_search = 1
                    break

                driver.get(next_page_url)
                time.sleep(sleep_sec)
            else:

                print('\n기사 수집을 완료하였습니다. \n')
                time.sleep(sleep_sec)
                break

        # 모든 뉴스를 다 찾았을때
        if all_search == 1:
            print("※ 요청하신 기사의 수보다 기사가 부족합니다.\n다음 언론사에서 검색합니다.")

            newsCount = org_news_num

            # driver.quit()
            # time.sleep(2)

            continue
        elif no_exist == 1:

            newsCount = org_news_num
            #
            # driver.quit()
            # time.sleep(2)
            continue

        newsCount = org_news_num

    driver.close()
    time.sleep(5)

    return news_dict


# 크롤링 전 사전 데이터 입력
def naver_crawler():
    # 테이블명 : 크롤링 한 날짜
    date = str(datetime.now())
    date = date[:date.rfind(' ')]

    ### 데베에서 키워드 읽어오기
    dynamodb = boto3.resource('dynamodb')

    # 고정 키워드 가져오기
    table_keyword = dynamodb.Table('KEYWORD')

    # 고정키워드 가져오기
    response_fix = table_keyword.query(
        KeyConditionExpression=Key('DATE').eq(date) & Key('TYPE_ID').begins_with('FIX')
    )
    item_fix = response_fix['Items']

    # 일일키워드 가져오기
    response_day = table_keyword.query(
        KeyConditionExpression=Key('DATE').eq(date) & Key('TYPE_ID').begins_with('DAY')
    )
    item_day = response_day['Items']

    keywords_fix = []
    keywords_day = []

    # 가져온 키워드들 리스트로 저장
    for fix, day in zip(item_fix, item_day):
        keywords_fix.append(fix['VALUE'])
        keywords_day.append(day['VALUE'])

    keywords = keywords_fix + keywords_day
    ###

    newsCount = 20  # 언론사별 뉴스크롤링 갯수

    print('\n' + '=' * 25 + "START CRAWLING" + '=' * 25 + '\n')

    # with ThreadPoolExecutor(max_workers=8) as executor:
    #     #crl_dict = crawling_func(keyword, newsCount, pressList2)
    #     crl_dict = [executor.submit(crawling_func, keyword, newsCount, pressList1) for keyword in keywords]

    # for future in as_completed(crl_dict):
    # #for i in crl_dict.values():
    #     result = future.result()
    #     for i in result.values():
    #         news_dict[dict_idx] = i
    #         dict_idx += 1

    ### 크롤링 시작작
    now = datetime.now()

    if now.hour + 9 > 24:
        nowhour = now.hour + 9 - 24
    else:
        nowhour = now.hour + 9

    # 딕셔너리 형식으로 뉴스 저장
    news_dict = {}
    dict_idx = 0  # 뉴스갯수

    # 키워드 크롤링
    # if nowhour == 18 and now.minute < 16:
    with ThreadPoolExecutor(max_workers=8) as executor:
        # crl_dict = crawling_func(keyword, newsCount, pressList2)
        crl_dict = [executor.submit(crawling_func, keyword, newsCount, pressList1) for keyword in keywords[0:4]]

    for future in as_completed(crl_dict):
        result = future.result()
        for i in result.values():
            news_dict[dict_idx] = i
            dict_idx += 1
    ###

    # 최종적으로 복합키워드를 가져와주는 리스트 (ex. {[금리,대출]:30, [금리,대출,아파트]:10, [부동산,아파트]:51} 이런 형태)
    mixed_keyword_list = {("dumy", "yeah"): 0}

    for key, value in news_dict.items():
        temp_list = list()
        content = value['content']
        for total_keyword in keywords:
            if total_keyword in content:
                temp_list.append(total_keyword)
                # 가져온 고정,일일 키워드 중, 기사 본문에 2개 이상 나왔을 시,
                if len(temp_list) >= 2:
                    temp_tuple = tuple(temp_list)
                    if temp_tuple in mixed_keyword_list.key():  # 이미 존재할 시,
                        mixed_keyword_list[temp_tuple] += 1
                    else:  # 존재하지 않을 시,
                        mixed_keyword_list[temp_tuple] = 1

    # 많이나온 상위 5개를 이러한 형태로 출력
    # 최종적으로 DynamoDB로 옮겨져야하는 변수는 mixed_keyword
    # 딕셔너리를 값(value)을 기준으로 내림차순으로 정렬합니다.
    sorted_data = sorted(mixed_keyword_list.items(), key=lambda x: x[1], reverse=True)

    # 상위 5개의 항목을 추출하고, 각 항목을 리스트로 변환합니다.
    # [['금리', '대출'], ['추석', '연휴'], ['미국', '중국'], ['금리', '미국'], ['서울', '한국']] 이러한 형태를 띈다.
    mixed_keyword = [list(key) for key, value in sorted_data[:5]]

    print(mixed_keyword)

    # 테이블 생성
    table = dynamodb.create_table(
        TableName=date,
        KeySchema=[
            {
                'AttributeName': 'keyword',
                'KeyType': 'HASH'
            },

            {
                "AttributeName": "id",
                "KeyType": "RANGE"
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'keyword',
                'AttributeType': 'S'
            },

            {
                "AttributeName": "id",
                "AttributeType": "S"
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )

    # 테이블 생성될 때때까지 대기
    table.meta.client.get_waiter('table_exists').wait(TableName=date)

    # 테이블에 저장
    ID = 0
    table = dynamodb.Table(date)
    with table.batch_writer() as batch:
        for i in news_dict.values():
            batch.put_item(
                Item={
                    'keyword': i['keyword'],
                    'id': str(ID),
                    'content': i['content'],
                    'thumbnail': i['thumbnail'],
                    'title': i['title'],
                    'url': i['url']
                }
            )
            ID += 1

    # elif nowhour == 18 and now.minute < 22:
    #     with ThreadPoolExecutor(max_workers=8) as executor:
    #         #crl_dict = crawling_func(keyword, newsCount, pressList2)
    #         crl_dict = [executor.submit(crawling_func, keyword, newsCount, pressList1) for keyword in keywords[2:4]]

    #     for future in as_completed(crl_dict):
    #     #for i in crl_dict.values():
    #         result = future.result()
    #         for i in result.values():
    #             news_dict[dict_idx] = i
    #             dict_idx += 1

    #     # 테이블에 저장
    #     ID = 0
    #     table = dynamodb.Table(date)
    #     with table.batch_writer() as batch:
    #         for i in news_dict.values():
    #             batch.put_item(
    #                 Item={
    #                     'keyword': i['keyword'],
    #                     'id': str(ID),
    #                     'content': i['content'],
    #                     'thumbnail': i['thumbnail'],
    #                     'title': i['title'],
    #                     'url': i['url']
    #                 }
    #             )
    #             ID += 1

    # elif nowhour == 22 and now.minute < 48:
    #     for keyword in keywords:
    #         crl_dict = crawling_func(keyword, newsCount, pressList3)
    #         for i in crl_dict.values():
    #             news_dict[dict_idx] = i
    #             dict_idx += 1

    #     # 테이블에 저장
    #     ID = 0
    #     table = dynamodb.Table(date)
    #     with table.batch_writer() as batch:
    #         for i in news_dict.values():
    #             batch.put_item(
    #                 Item={
    #                     'keyword': i['keyword'],
    #                     'ID': str(ID),
    #                     'content': i['content'],
    #                     'title': i['title'],
    #                     'url': i['url']
    #                 }
    #             )
    #             ID += 1

    # elif nowhour == 23 and now.minute < 4:
    #     for keyword in keywords:
    #         crl_dict = crawling_func(keyword, newsCount, pressList4)
    #         for i in crl_dict.values():
    #             news_dict[dict_idx] = i
    #             dict_idx += 1

    #     # 테이블에 저장
    #     ID = 0
    #     table = dynamodb.Table(date)
    #     with table.batch_writer() as batch:
    #         for i in news_dict.values():
    #             batch.put_item(
    #                 Item={
    #                     'keyword': i['keyword'],
    #                     'ID': str(ID),
    #                     'content': i['content'],
    #                     'title': i['title'],
    #                     'url': i['url']
    #                 }
    #             )
    #             ID += 1
