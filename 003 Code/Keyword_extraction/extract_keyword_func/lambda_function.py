import json
import numpy as np

# 데베
import boto3
from boto3.dynamodb.conditions import Key, Attr  # 데베에서 값 가져오기 가져오기

# 로컬 코드 import

# Import Python Library
from datetime import datetime
import time


def lambda_handler(event, context):
    # TODO implement

    # 당일 크롤링 한 날짜
    date = str(datetime.now())
    date = date[:date.rfind(' ')]

    ### 현재 시간 한국 기준으로 변경(UTC + 9시간)
    now = datetime.now()

    if now.hour + 9 > 24:
        nowhour = now.hour + 9 - 24
    else:
        nowhour = now.hour + 9

    nowhour_cust = 21  # 21시
    nowmin_cust = 8  # 8분
    ###

    # Day_Extract_Keyword_0to5 호출
    if nowhour == nowhour_cust - 1 and now.minute < nowmin_cust + 50:
        a = 1

    # Day_Extract_Keyword_6to9 호출
    elif nowhour == nowhour_cust and now.minute < nowmin_cust:
        a = 2

    # Day_Extract_Keyword_10to13 호출
    elif nowhour == nowhour_cust and now.minute < nowmin_cust + 10:
        a = 3

    # Day_Extract_Keyword_14to17 호출
    elif nowhour == nowhour_cust and now.minute < nowmin_cust + 20:
        a = 4

    # Day_Extract_Keyword_18to21 호출
    elif nowhour == nowhour_cust and now.minute < nowmin_cust + 30:
        a = 5

    # Day_Extract_Keyword_22to23 호출
    elif nowhour == nowhour_cust and now.minute < nowmin_cust + 40:
        a = 6

    # KEYWORD, WORDCLOUD 테이블에 저장
    elif nowhour == nowhour_cust and now.minute < nowmin_cust + 50:
        a = 7

    ### 1일전까지의 뉴스기사 크롤링
    if a == 1:
        from day_extrac_dir.Day_Extract_Keyword_0to5 import DayKeywordCrawler_0to5

        keywordData_0to5, newsCount_0to5 = DayKeywordCrawler_0to5()  # ~ 5시간전 나오면 종료 크롤러
        keywordData_0to5 = keywordData_0to5[:30]  # 30개만 사용용

        ### 모든 워드클라우드의 정보들을 다 더하기
        total_dict = dict()

        # ~ 5시간전
        for item in keywordData_0to5:
            keyword = item[0]  # 첫번째 원소가 키워드
            count = item[1]  # 두번째 원소가 횟수
            if keyword in total_dict:
                total_dict[keyword] += count
            else:
                total_dict[keyword] = count
        ###

        # 내림차순으로 정렬
        sorted_keywordDatas = sorted(total_dict.items(), key=lambda x: x[1], reverse=True)

        # 정렬키 구분 ID
        DAY_ID = 0

    elif a == 2:
        from day_extrac_dir.Day_Extract_Keyword_6to9 import DayKeywordCrawler_6to9

        keywordData_6to9, newsCount_6to9 = DayKeywordCrawler_6to9()  # 6 ~ 9시간전 나오면 종료 크롤러
        keywordData_6to9 = keywordData_6to9[:30]  # 30개만 사용

        ### 모든 워드클라우드의 정보들을 다 더하기
        total_dict = dict()

        # 6 ~ 9시간전
        for item in keywordData_6to9:
            keyword = item[0]  # 첫번째 원소가 키워드
            count = item[1]  # 두번째 원소가 횟수
            if keyword in total_dict:
                total_dict[keyword] += count
            else:
                total_dict[keyword] = count
        ###

        # 내림차순으로 정렬
        sorted_keywordDatas = sorted(total_dict.items(), key=lambda x: x[1], reverse=True)

        # 정렬키 구분 ID
        DAY_ID = 30

    elif a == 3:
        from day_extrac_dir.Day_Extract_Keyword_10to13 import DayKeywordCrawler_10to13

        keywordData_10to13, newsCount_10to13 = DayKeywordCrawler_10to13()  # 10 ~ 13시간전 나오면 종료 크롤러
        keywordData_10to13 = keywordData_10to13[:30]  # 30개만 사용

        #### 모든 워드클라우드의 정보들을 다 더하기
        total_dict = dict()

        # 10 ~ 13시간전
        for item in keywordData_10to13:
            keyword = item[0]  # 첫번째 원소가 키워드
            count = item[1]  # 두번째 원소가 횟수
            if keyword in total_dict:
                total_dict[keyword] += count
            else:
                total_dict[keyword] = count
        ###

        # 내림차순으로 정렬
        sorted_keywordDatas = sorted(total_dict.items(), key=lambda x: x[1], reverse=True)

        # 정렬키 구분 ID
        DAY_ID = 60

    elif a == 4:
        from day_extrac_dir.Day_Extract_Keyword_14to17 import DayKeywordCrawler_14to17

        keywordData_14to17, newsCount_14to17 = DayKeywordCrawler_14to17()  # 14 ~ 17시간전 나오면 종료 크롤러
        keywordData_14to17 = keywordData_14to17[:30]  # 30개만 사용

        ### 모든 워드클라우드의 정보들을 다 더하기
        total_dict = dict()

        # 14 ~ 17시간전
        for item in keywordData_14to17:
            keyword = item[0]  # 첫번째 원소가 키워드
            count = item[1]  # 두번째 원소가 횟수
            if keyword in total_dict:
                total_dict[keyword] += count
            else:
                total_dict[keyword] = count
        ###

        # 내림차순으로 정렬
        sorted_keywordDatas = sorted(total_dict.items(), key=lambda x: x[1], reverse=True)

        # 정렬키 구분 ID
        DAY_ID = 90

    elif a == 5:
        from day_extrac_dir.Day_Extract_Keyword_18to21 import DayKeywordCrawler_18to21

        keywordData_18to21, newsCount_18to21 = DayKeywordCrawler_18to21()  # 18 ~ 21시간전 나오면 종료 크롤러
        keywordData_18to21 = keywordData_18to21[:30]  # 30개만 사용

        ### 모든 워드클라우드의 정보들을 다 더하기
        total_dict = dict()

        # 18 ~ 21시간전
        for item in keywordData_18to21:
            keyword = item[0]  # 첫번째 원소가 키워드
            count = item[1]  # 두번째 원소가 횟수
            if keyword in total_dict:
                total_dict[keyword] += count
            else:
                total_dict[keyword] = count
        ###

        # 내림차순으로 정렬
        sorted_keywordDatas = sorted(total_dict.items(), key=lambda x: x[1], reverse=True)

        # 정렬키 구분 ID
        DAY_ID = 120

    elif a == 6:
        from day_extrac_dir.Day_Extract_Keyword_22to23 import DayKeywordCrawler_22to23

        keywordData_22to23, newsCount_22to23 = DayKeywordCrawler_22to23()  # 22 ~ 23시간전 나오면 종료 크롤러
        keywordData_22to23 = keywordData_22to23[:30]  # 30개만 사용

        ### 모든 워드클라우드의 정보들을 다 더하기
        total_dict = dict()

        # 22 ~ 23시간전
        for item in keywordData_22to23:
            keyword = item[0]  # 첫번째 원소가 키워드
            count = item[1]  # 두번째 원소가 횟수
            if keyword in total_dict:
                total_dict[keyword] += count
            else:
                total_dict[keyword] = count
        ###

        # 내림차순으로 정렬
        sorted_keywordDatas = sorted(total_dict.items(), key=lambda x: x[1], reverse=True)

        # 정렬키 구분 ID
        DAY_ID = 150
    ###

    # ALLWORDCLOUD에 저장된 값으로 주간,wordcloud에 사용할 값 만들고 테이블에 저장장
    elif a == 7:
        # dynamodb 호출 및 생성성
        dynamodb = boto3.resource('dynamodb')

        # 테이블 호출 : KEYWORD(읽기로 사용)
        table_keyword = dynamodb.Table('KEYWORD')

        ### KEYWORD 테이블에서 당일 고정 키워드 가져오기
        response_fix = table_keyword.query(
            KeyConditionExpression=Key('DATE').eq(date) & Key('TYPE_ID').begins_with('FIX')
        )

        item = response_fix['Items']
        fixedKeywords = []

        for i in item:
            fixedKeywords.append(i['VALUE'])
        ###

        # 테이블 호출 : ALLWORDCLOUD(읽기로 사용)
        table_allwordcloud = dynamodb.Table('ALLWORDCLOUD')

        # 당일의 모든 아이텔 읽기
        response_allwordcloud = table_allwordcloud.query(
            KeyConditionExpression=Key('DATE').eq(date)
        )

        allwordcloud_list = []  # 호출한 ALLWORDCLOUD 테이블값
        dayKeywords = []  # 사용될 ALLWORDCLOUD 테이블값

        for i in response_allwordcloud['Items']:
            allwordcloud_list.append([i['VALUE'], i['COUNT']])

        dayKeywords = allwordcloud_list.copy()

        pop_list = []  # 중복된 키워드
        for n_1, j in enumerate(allwordcloud_list):

            # 중복된 키워드 발견 시 제일 앞 인덱스의 나온 수에 모두 더하고 남은 중북 인덱스들을 따로 저장
            for n_2, k in enumerate(allwordcloud_list):
                if j[0] == k[0] and n_1 != n_2 and n_1 < n_2:
                    dayKeywords[n_1][1] += dayKeywords[n_2][1]
                    pop_list.append(n_2)

        # 중복 인덱스들로 중복 키워드 제거( [키워드, 숫자] 형태이기 때문에 remove 사용해도 무방)
        for del_idx in pop_list:
            try:
                dayKeywords.remove(allwordcloud_list[del_idx])
            except:
                continue

        dayKeywords = sorted(dayKeywords, key=lambda x: x[1], reverse=True)

        # 고정키워드와 겹치는 경우가 있을경우 제거
        dayKeyword_duplication_del = dayKeywords.copy()
        for idx, element in enumerate(fixedKeywords):
            for dupli_keyword in dayKeywords:
                if element in dupli_keyword[0]:
                    dayKeyword_duplication_del.remove(dupli_keyword)

        # 제거되고 남은 것들 중, 10개만 추려낸다.
        dayKeywords = dayKeyword_duplication_del[:10]

        # 테이블에 저장(KEYWORD)
        DAY_ID = 0
        table = dynamodb.Table('KEYWORD')
        with table.batch_writer() as batch:
            for dayKeyword in dayKeywords:
                batch.put_item(
                    Item={
                        'DATE': date,
                        'TYPE_ID': 'DAY_{}'.format(DAY_ID),
                        'VALUE': dayKeyword[0]
                    }
                )
                DAY_ID += 1

        wordcloudDatas = dayKeyword_duplication_del[:15]

        # 테이블에 저장(WORDCLOUD)
        DAY_ID = 0
        table = dynamodb.Table('WORDCLOUD')
        with table.batch_writer() as batch:
            for wordcloudData in wordcloudDatas:
                batch.put_item(
                    Item={
                        'DATE': date,
                        'DAY_ID': 'DAY_{}'.format(DAY_ID),
                        'COUNT': wordcloudData[1],
                        'VALUE': wordcloudData[0]
                    }
                )
                DAY_ID += 1

        return

    # a = 1 ~ 6까지의 값 테이블에 저장장
    dynamodb = boto3.resource('dynamodb')

    table = dynamodb.Table('ALLWORDCLOUD')
    with table.batch_writer() as batch:
        for sorted_keywordData in sorted_keywordDatas:
            batch.put_item(
                Item={
                    'DATE': date,
                    'DAY_ID': 'DAY_{}'.format(DAY_ID),
                    'COUNT': sorted_keywordData[1],
                    'VALUE': sorted_keywordData[0]
                }
            )
            DAY_ID += 1

