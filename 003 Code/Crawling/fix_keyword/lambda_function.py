import json
import numpy as np

# 데베
import boto3

# 로컬 모듈 impoprt
from Fixed_Extract_Keyword import FixedKeywordCrawler

# 시간 관련 라이브러리리
from datetime import datetime
import time


def lambda_handler(event, context):
    # TODO implement

    # 고정 키워드를 추출
    # Python list 형태로 10개의 고정 키워드를 추출한다 (통계청 - 뉴스기반검색 경제 키워드 이용)

    print("======= 고정 키워드 크롤링을 시작합니다 =======")
    fixedKeywords = FixedKeywordCrawler()
    print("- 고정 키워드")
    print(fixedKeywords)
    print("======= 고정 키워드 크롤링을 마칩니다. =======")
    print('\n')

    ### 데베에 저장

    # 테이블명 : 크롤링 한 날짜
    date = str(datetime.now())
    date = date[:date.rfind(' ')]

    dynamodb = boto3.resource('dynamodb')

    # 테이블에 저장(고정 키워드)
    FIX_ID = 0
    table = dynamodb.Table('KEYWORD')
    with table.batch_writer() as batch:
        for fixedKeyword in fixedKeywords:
            batch.put_item(
                Item={
                    'DATE': date,
                    'TYPE_ID': 'FIX_{}'.format(FIX_ID),
                    'VALUE': fixedKeyword
                }
            )
            FIX_ID += 1
