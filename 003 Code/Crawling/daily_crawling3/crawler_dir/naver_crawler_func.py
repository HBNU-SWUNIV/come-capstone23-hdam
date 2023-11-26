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

pressList1 = ['매일경제', '뉴시스', '연합뉴스', '한국경제', 'KBS']


def crawling_func(keyword, newsCount, pressList):
    end_this_keyword_crawling = 0  # 경제 관련 뉴스가 수집 뉴스 수 보다 많을 때 해당 키워드는 넘어가기

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
    # time.sleep(sleep_sec)

    #### 옵션 클릭
    search_opn_btn = driver.find_element(By.XPATH, '//a[@class="btn_option _search_option_open_btn"]')
    search_opn_btn.click()
    time.sleep(sleep_sec)

    #### 기간(순서 중요, 기간, 언론사 등 선택 후 -> 정렬 선택)
    bx_term = driver.find_element(By.XPATH,
                                  '//div[@role="listbox" and @class="mod_group_option_sort _search_option_detail_wrap"]//li[@class="bx term"]')

    # 1일까지
    term_tablist = bx_term.find_elements(By.XPATH, './/div[@role="tablist" and @class="option"]/a')

    driver.implicitly_wait(10)  # 유독 여기에서 오류가 남

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
        needless_keyword = 0  # 경제와 관련 없는 키워드면 그냥 다음으로 넘어가기기

        if end_this_keyword_crawling == 3:
            driver.close()
            time.sleep(4)

            print("경제 관련 키워드가 아닙니다.")
            news_dict = {0: {'title': 'not economy'}}

            return news_dict
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
        # time.sleep(sleep_sec)

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
                    needless_keyword += 1
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

            elif needless_keyword > newsCount:
                end_this_keyword_crawling += 1
                break

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
    time.sleep(2)

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
        KeyConditionExpression=Key('DATE').eq(date)
    )
    item_keyword = response_fix['Items']

    keywords_DB = []

    # 가져온 키워드들 리스트로 저장
    for item in item_keyword:
        if "MIX" in item['TYPE_ID']:
            continue
        else:
            keywords_DB.append(item['VALUE'])
    ###

    newsCount = 30  # 언론사별 뉴스크롤링 갯수

    ### 크롤링 시작

    # 현재 시간 한국 기준으로 변경
    now = datetime.now()

    if now.hour + 9 > 24:
        nowhour = now.hour + 9 - 24
    else:
        nowhour = now.hour + 9

    # 딕셔너리 형식으로 뉴스 저장
    news_dict_db = {}
    dict_idx_db = 0  # 뉴스갯수

    # 테이블명 : 크롤링 한 날짜
    date = str(datetime.now())
    date = date[:date.rfind(' ')]

    # 테이블 생성
    dynamodb = boto3.resource('dynamodb')

    nowhour_cust = 22  # 22시(10시)
    nowmin_cust = 18  # 18분

    # 키워드 크롤링 #
    if nowhour == nowhour_cust and now.minute < nowmin_cust:
        with ThreadPoolExecutor(max_workers=8) as executor:
            # crl_dict = crawling_func(keyword, newsCount, pressList2)
            crl_dict = [executor.submit(crawling_func, keyword, newsCount, pressList1) for keyword in keywords_DB[0:3]]

        for future in as_completed(crl_dict):
            result = future.result()

            for i in result.values():
                if i == 'not economy':
                    break

                news_dict_db[dict_idx_db] = i
                dict_idx_db += 1

        # 테이블에 저장
        table_db = dynamodb.Table(date)

        ID = 0
        with table_db.batch_writer() as batch:
            # batch._flush_amount = 1 # 이거 해야 재귀 오류 안 안뜸
            for i in news_dict_db.values():
                item = {}
                item['KEYWORD'] = i['keyword']
                item['ID'] = str(ID)
                item['CONTENT'] = i['content']
                item['THUMBNAIL'] = i['thumbnail']
                item['TITLE'] = i['title']
                item['URL'] = i['url']
                item['AGENCY'] = i['agency']

                batch.put_item(Item=item)

                ID += 1

    elif nowhour == nowhour_cust and now.minute < nowmin_cust + 5:
        with ThreadPoolExecutor(max_workers=8) as executor:
            # crl_dict = crawling_func(keyword, newsCount, pressList2)
            crl_dict = [executor.submit(crawling_func, keyword, newsCount, pressList1) for keyword in keywords_DB[3:6]]

        for future in as_completed(crl_dict):
            result = future.result()

            for i in result.values():
                if i == 'not economy':
                    break

                news_dict_db[dict_idx_db] = i
                dict_idx_db += 1

        # 테이블에 저장
        table_db = dynamodb.Table(date)

        ID = 0
        with table_db.batch_writer() as batch:
            # batch._flush_amount = 1 # 이거 해야 재귀 오류 안 안뜸
            for i in news_dict_db.values():
                item = {}
                item['KEYWORD'] = i['keyword']
                item['ID'] = str(ID)
                item['CONTENT'] = i['content']
                item['THUMBNAIL'] = i['thumbnail']
                item['TITLE'] = i['title']
                item['URL'] = i['url']
                item['AGENCY'] = i['agency']

                batch.put_item(Item=item)

                ID += 1

    elif nowhour == nowhour_cust and now.minute < nowmin_cust + 10:
        with ThreadPoolExecutor(max_workers=8) as executor:
            # crl_dict = crawling_func(keyword, newsCount, pressList2)
            crl_dict = [executor.submit(crawling_func, keyword, newsCount, pressList1) for keyword in keywords_DB[6:9]]

        for future in as_completed(crl_dict):
            result = future.result()

            for i in result.values():
                if i == 'not economy':
                    break

                news_dict_db[dict_idx_db] = i
                dict_idx_db += 1

        # 테이블에 저장
        table_db = dynamodb.Table(date)

        ID = 0
        with table_db.batch_writer() as batch:
            # batch._flush_amount = 1 # 이거 해야 재귀 오류 안 안뜸
            for i in news_dict_db.values():
                item = {}
                item['KEYWORD'] = i['keyword']
                item['ID'] = str(ID)
                item['CONTENT'] = i['content']
                item['THUMBNAIL'] = i['thumbnail']
                item['TITLE'] = i['title']
                item['URL'] = i['url']
                item['AGENCY'] = i['agency']

                batch.put_item(Item=item)

                ID += 1

    elif nowhour == nowhour_cust and now.minute < nowmin_cust + 15:
        with ThreadPoolExecutor(max_workers=8) as executor:
            # crl_dict = crawling_func(keyword, newsCount, pressList2)
            crl_dict = [executor.submit(crawling_func, keyword, newsCount, pressList1) for keyword in keywords_DB[9:12]]

        for future in as_completed(crl_dict):
            result = future.result()

            for i in result.values():
                if i == 'not economy':
                    break

                news_dict_db[dict_idx_db] = i
                dict_idx_db += 1

        # 테이블에 저장
        table_db = dynamodb.Table(date)

        ID = 0
        with table_db.batch_writer() as batch:
            # batch._flush_amount = 1 # 이거 해야 재귀 오류 안 안뜸
            for i in news_dict_db.values():
                item = {}
                item['KEYWORD'] = i['keyword']
                item['ID'] = str(ID)
                item['CONTENT'] = i['content']
                item['THUMBNAIL'] = i['thumbnail']
                item['TITLE'] = i['title']
                item['URL'] = i['url']
                item['AGENCY'] = i['agency']

                batch.put_item(Item=item)

                ID += 1

    elif nowhour == nowhour_cust and now.minute < nowmin_cust + 20:
        with ThreadPoolExecutor(max_workers=8) as executor:
            # crl_dict = crawling_func(keyword, newsCount, pressList2)
            crl_dict = [executor.submit(crawling_func, keyword, newsCount, pressList1) for keyword in
                        keywords_DB[12:15]]

        for future in as_completed(crl_dict):
            result = future.result()

            for i in result.values():
                if i == 'not economy':
                    break

                news_dict_db[dict_idx_db] = i
                dict_idx_db += 1

        # 테이블에 저장
        table_db = dynamodb.Table(date)

        ID = 0
        with table_db.batch_writer() as batch:
            # batch._flush_amount = 1 # 이거 해야 재귀 오류 안 안뜸
            for i in news_dict_db.values():
                item = {}
                item['KEYWORD'] = i['keyword']
                item['ID'] = str(ID)
                item['CONTENT'] = i['content']
                item['THUMBNAIL'] = i['thumbnail']
                item['TITLE'] = i['title']
                item['URL'] = i['url']
                item['AGENCY'] = i['agency']

                batch.put_item(Item=item)

                ID += 1

    elif nowhour == nowhour_cust and now.minute < nowmin_cust + 25:
        with ThreadPoolExecutor(max_workers=8) as executor:
            # crl_dict = crawling_func(keyword, newsCount, pressList2)
            crl_dict = [executor.submit(crawling_func, keyword, newsCount, pressList1) for keyword in
                        keywords_DB[15:18]]

        for future in as_completed(crl_dict):
            result = future.result()

            for i in result.values():
                if i == 'not economy':
                    break

                news_dict_db[dict_idx_db] = i
                dict_idx_db += 1

        # 테이블에 저장
        table_db = dynamodb.Table(date)

        ID = 0
        with table_db.batch_writer() as batch:
            # batch._flush_amount = 1 # 이거 해야 재귀 오류 안 안뜸
            for i in news_dict_db.values():
                item = {}
                item['KEYWORD'] = i['keyword']
                item['ID'] = str(ID)
                item['CONTENT'] = i['content']
                item['THUMBNAIL'] = i['thumbnail']
                item['TITLE'] = i['title']
                item['URL'] = i['url']
                item['AGENCY'] = i['agency']

                batch.put_item(Item=item)

                ID += 1

    elif nowhour == nowhour_cust and now.minute < nowmin_cust + 30:
        with ThreadPoolExecutor(max_workers=8) as executor:
            # crl_dict = crawling_func(keyword, newsCount, pressList2)
            crl_dict = [executor.submit(crawling_func, keyword, newsCount, pressList1) for keyword in
                        keywords_DB[18:20]]

        for future in as_completed(crl_dict):
            result = future.result()

            for i in result.values():
                if i == 'not economy':
                    break

                news_dict_db[dict_idx_db] = i
                dict_idx_db += 1

        # 테이블에 저장
        table_db = dynamodb.Table(date)

        ID = 0
        with table_db.batch_writer() as batch:
            # batch._flush_amount = 1 # 이거 해야 재귀 오류 안 안뜸
            for i in news_dict_db.values():
                item = {}
                item['KEYWORD'] = i['keyword']
                item['ID'] = str(ID)
                item['CONTENT'] = i['content']
                item['THUMBNAIL'] = i['thumbnail']
                item['TITLE'] = i['title']
                item['URL'] = i['url']
                item['AGENCY'] = i['agency']

                batch.put_item(Item=item)

                ID += 1
    else:
        print("에휴휴")

