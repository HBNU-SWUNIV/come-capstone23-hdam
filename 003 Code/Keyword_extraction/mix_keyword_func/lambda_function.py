import json

import time
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Key, Attr


def lambda_handler(event, context):
    # TODO implement

    # 당일 날짜(미국 기준이라 우리나라랑 9시간 차이, 아침 9시 까진 어제 날짜가 나옴옴)
    date = str(datetime.now())
    date = date[:date.rfind(' ')]

    # DynamoDB 클라이언트 생성
    dynamodb = boto3.resource('dynamodb')

    ###
    # 고정, 일일 키워드 테이블 불러오기
    table_keyword = dynamodb.Table('KEYWORD')

    # 당일의 키워드만 가져오기
    response = table_keyword.query(
        KeyConditionExpression=Key('DATE').eq(date)
    )
    item_keyword = response['Items']

    keywords_DB = []  # 키워드 저장할 리스트
    keywords_id = []

    # 가져온 키워드들 리스트로 저장
    for item in item_keyword:
        if "MIX" in item['TYPE_ID']:
            continue
        else:
            keywords_DB.append(item['VALUE'])
            keywords_id.append(item['TYPE_ID'])
    ###

    ###
    # 뉴스기사 테이블 불러오기
    table = dynamodb.Table(date)

    n = 0  # 뉴스기사 갯수
    news_dict = {}  # 기사 본문 저장할 딕셔너리

    fin_keywords = keywords_DB.copy()

    # 뉴스기사 테이블에서 모든 뉴스기사 가져오기
    for keyword, id in zip(keywords_DB, keywords_id):
        items = []  # 테이블 값

        # 키워드에 대한 쿼리
        response = table.query(
            KeyConditionExpression=Key('KEYWORD').eq(keyword)
        )

        if response['Items'] == []:
            # 해당 기본 키를 가진 항목을 삭제합니다.
            key_to_delete = {
                'DATE': date,
                'TYPE_ID': id
            }

            response = table_keyword.delete_item(
                Key=key_to_delete
            )

            fin_keywords.remove(keyword)

            continue

        # item값 저장
        items = response['Items']

        for item in items:
            news_dict[n] = {
                'content': item['CONTENT']
            }
            n += 1
    ###

    ###
    # 최종적으로 복합키워드를 가져와주는 리스트 (ex. {[금리,대출]:30, [금리,대출,아파트]:10, [부동산,아파트]:51} 이런 형태)
    mixed_keyword_dict = {("dumy", "yeah"): 0}  # 해달 딕셔너리가 비어있으면 오류남남

    for key, value in news_dict.items():
        temp_list = list()
        content = value['content']
        for total_keyword in fin_keywords:
            if total_keyword in content:
                temp_list.append(total_keyword)
                # 가져온 고정,일일 키워드 중, 기사 본문에 2개 이상 나왔을 시,
                if len(temp_list) >= 2 and len(temp_list) <= 3:
                    temp_tuple = tuple(temp_list)
                    if temp_tuple in mixed_keyword_dict.keys():  # 이미 존재할 시,
                        mixed_keyword_dict[temp_tuple] += 1
                    else:  # 존재하지 않을 시,
                        mixed_keyword_dict[temp_tuple] = 1

    # 많이나온 상위 5개를 이러한 형태로 출력
    # 최종적으로 DynamoDB로 옮겨져야하는 변수는 mixed_keyword
    # 딕셔너리를 값(value)을 기준으로 내림차순으로 정렬합니다.
    sorted_data = sorted(mixed_keyword_dict.items(), key=lambda x: x[1], reverse=True)

    # 상위 5개의 항목을 추출하고, 각 항목을 리스트로 변환합니다.
    # [['금리', '대출'], ['추석', '연휴'], ['미국', '중국'], ['금리', '미국'], ['서울', '한국']] 이러한 형태를 띈다.
    pre_mixed_keywords = [list(key) for key, value in sorted_data[:10]]

    # 간혹 [부동산, 아파트], [부동산, 아파트, 금리] 이런식으로 너무 겹치는 키워드가 나오는거 방지
    dumy_mixed_keywords = pre_mixed_keywords.copy()  # 더비 키워드
    mixed_keywords = pre_mixed_keywords.copy()  # 실제 사용될 복합키워드
    del_mix_keyword = []

    for i in pre_mixed_keywords:
        for j in dumy_mixed_keywords:
            if " ".join(i) == " ".join(j):
                continue
            elif " ".join(i) in " ".join(j):
                del_mix_keyword.append(j)

    del_mix_keyword_set = set(tuple(item) for item in del_mix_keyword)
    for k in del_mix_keyword_set:
        print(k)
        mixed_keywords.remove(list(k))

    mixed_keywords_plus = []
    mix_str = ""

    for i in mixed_keywords:

        for j in i:
            mix_str = mix_str + j + " "
        mix_str = mix_str.strip().replace(" ", "&")
        mixed_keywords_plus.append(mix_str)
        mix_str = ""

    print(mixed_keywords_plus)

    # 테이블에 저장(복합합 키워드)
    MIX_ID = 0
    table_mixkeyword = dynamodb.Table('ALLMIXKEYWORD')
    with table_mixkeyword.batch_writer() as batch:
        for mixed_keyword in mixed_keywords_plus:
            batch.put_item(
                Item={
                    'DATE': date,
                    'MIX_ID': 'MIX_{}'.format(MIX_ID),
                    'VALUE': mixed_keyword,
                    'COUNT': MIX_ID
                }
            )
            MIX_ID += 1
    ###
