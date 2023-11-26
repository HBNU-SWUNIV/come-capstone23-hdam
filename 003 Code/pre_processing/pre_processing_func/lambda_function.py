import json

import time
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr
import boto3

import news_relation_analysis as nraf
from PyKomoran import *


def lambda_handler(event, context):
    # TODO implement

    # Pykomoran 사용용
    komoran = Komoran(DEFAULT_MODEL['FULL'])

    # 당일 크롤링 한 날짜
    date = str(datetime.now())
    date = date[:date.rfind(' ')]

    # DynamoDB 클라이언트 생성
    dynamodb = boto3.resource('dynamodb')

    # ALLMIXKEYWORD 테이블 호출
    table_mixkeyword = dynamodb.Table('ALLMIXKEYWORD')

    # 모든 키워드 가져오기
    response_mix = table_mixkeyword.query(
        KeyConditionExpression=Key('DATE').eq(date)
    )
    item_mix = response_mix['Items']

    ### 복합키워드를 각각의 키워드로 분리리
    mix_list = []

    for i in item_mix:
        dumy_str = i["VALUE"] + "&" + str(i["COUNT"])
        keywords = dumy_str.split("&")

        mix_list.append(keywords)
    ###

    mix_list = sorted(mix_list, key=lambda x: x[2], reverse=False)

    ### 크롤링 테이블의 모든 데이터를 가져옴
    table = dynamodb.Table(date)

    count = 0  # 상위 5개의 복합키워드만 추출

    for keywords in mix_list:
        keywords = keywords[:2]

        if count == 5: break

        n = 0  # 뉴스 갯수
        news_dict = {}  # 뉴스 정보 저장할 딕셔너리

        items = []
        for keyword in keywords:
            # 키워드에 대한 쿼리리
            response = table.query(
                KeyConditionExpression=Key('KEYWORD').eq(keyword)
            )

            # 결과 합치기
            items = items + response['Items']

        for item in items:
            news_dict[n] = {'keyword': item['KEYWORD'],
                            'title': item['TITLE'],
                            'content': item['CONTENT'],
                            'url': item['URL'],
                            'thumbnail': item['THUMBNAIL']
                            }
            n += 1

        count = nraf.news_relation_analysis(news_dict, komoran, keywords, count)
    ###

    return
