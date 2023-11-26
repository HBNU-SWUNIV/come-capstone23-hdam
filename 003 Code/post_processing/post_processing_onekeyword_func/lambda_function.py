import json

import pandas as pd
import numpy as np
from PyKomoran import *
import math

import time
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key, Attr  # 테이블 읽기

from divrank import divrank
from split_korean_sentences_func import split_korean_sentences
import networkx as nx


def lambda_handler(event, context):
    # TODO implement
    dumy_count = 0

    komoran = Komoran(DEFAULT_MODEL['FULL'])

    # 테이블명 : 크롤링 한 날짜
    date = str(datetime.now())
    date = date[:date.rfind(' ')]

    ### 데베에서 키워드 읽어오기
    dynamodb = boto3.resource('dynamodb')

    # 고정 키워드 가져오기
    table_keyword = dynamodb.Table('KEYWORD')

    ### 시간에 따른 키워드별 가져오는게 다름
    now = datetime.now()

    if now.hour + 9 > 24:
        nowhour = now.hour + 9 - 24
    else:
        nowhour = now.hour + 9

    # 테이블 생성
    dynamodb = boto3.resource('dynamodb')

    nowhour_cust = 23  # 23시
    nowmin_cust = 32  # 32분

    ### 테스트용
    # # 고정 키워드 가져오기
    # response_keyword = table_keyword.query(
    #     KeyConditionExpression=Key('DATE').eq(date) & Key('TYPE_ID').begins_with('FIX')
    # )
    # item_keyword = response_keyword['Items']

    # # 일일키워드 가져오기
    # response_keyword = table_keyword.query(
    #     KeyConditionExpression=Key('DATE').eq(date) & Key('TYPE_ID').begins_with('DAY')
    # )
    # item_keyword = response_keyword['Items']
    ###

    # 고정키워드 가져오기
    if nowhour == nowhour_cust and now.minute < nowmin_cust:
        response_keyword = table_keyword.query(
            KeyConditionExpression=Key('DATE').eq(date) & Key('TYPE_ID').begins_with('FIX')
        )
        item_keyword = response_keyword['Items']

    elif nowhour == nowhour_cust and now.minute < nowmin_cust + 10:
        response_keyword = table_keyword.query(
            KeyConditionExpression=Key('DATE').eq(date) & Key('TYPE_ID').begins_with('FIX')
        )
        item_keyword = response_keyword['Items']

    # 일일키워드 가져오기
    elif nowhour == nowhour_cust and now.minute < nowmin_cust + 20:
        response_keyword = table_keyword.query(
            KeyConditionExpression=Key('DATE').eq(date) & Key('TYPE_ID').begins_with('DAY')
        )
        item_keyword = response_keyword['Items']

    # 일일키워드 가져오기
    elif nowhour == nowhour_cust + 1 and now.minute < nowmin_cust - 30:
        response_keyword = table_keyword.query(
            KeyConditionExpression=Key('DATE').eq(date) & Key('TYPE_ID').begins_with('DAY')
        )
        item_keyword = response_keyword['Items']

    else:
        pass

    keywords_DB = []
    keywords_ID = []

    # 가져온 키워드들 리스트로 저장
    for item in item_keyword:
        keywords_DB.append(item['VALUE'])
        keywords_ID.append(item['TYPE_ID'])
    ###

    ###
    # # 테스트용
    # a = 2

    # if a == 1:
    #     keywords_DB = keywords_DB[:5]
    #     keywords_ID = keywords_ID[:5]

    # elif a == 2:
    #     keywords_DB = keywords_DB[5:]
    #     keywords_ID = keywords_ID[5:]
    ###

    # 고정키워드 가져오기
    if nowhour == nowhour_cust and now.minute < nowmin_cust:
        keywords_DB = keywords_DB[:5]
        keywords_ID = keywords_ID[:5]

    elif nowhour == nowhour_cust and now.minute < nowmin_cust + 10:
        keywords_DB = keywords_DB[5:]
        keywords_ID = keywords_ID[5:]

    elif nowhour == nowhour_cust and now.minute < nowmin_cust + 20:
        keywords_DB = keywords_DB[:5]
        keywords_ID = keywords_ID[:5]

    elif nowhour == nowhour_cust + 1 and now.minute < nowmin_cust - 30:
        keywords_DB = keywords_DB[5:]
        keywords_ID = keywords_ID[5:]

    # DynamoDB 클라이언트 생성
    table = dynamodb.Table(date)

    n = 0
    news_dict = {}

    # 부동산에 대한 쿼리
    items = []
    for keyword in keywords_DB:
        response = table.query(
            KeyConditionExpression=Key('KEYWORD').eq(keyword)
        )

        items = items + response['Items']

    for item in items:
        news_dict[n] = {
            'keyword': item['KEYWORD'],
            'content': item['CONTENT']
        }

        n += 1
        # if n == 30: break

    for keyword, id in zip(keywords_DB, keywords_ID):
        no_keyword = 0
        sum_text = ""

        data = {}
        keyword_n = 0

        ### 없는 키워드 존재 시
        try:
            for i in news_dict.values():
                if i['keyword'] == keyword:
                    dumy_count = 1
        except:
            # 해당 기본 키를 가진 항목을 삭제합니다.
            # key_to_delete = {
            #     'DATE':date,
            #     'TYPE_ID':id
            # }

            # response = table_keyword.delete_item(
            #     Key=key_to_delete
            # )
            print("damn1")

            no_keyword = 1
        ###

        if no_keyword == 1:
            no_keyword = 0
            continue

        for i in news_dict.values():
            if i['keyword'] == keyword:
                data[keyword_n] = i
                keyword_n += 1

                if keyword_n == 20: break

        df = pd.DataFrame(data).T  # 엑셀로 실행할때 주석걸기

        try:
            df = df[df['content'].notnull()]  # Null값 데이터 없애기
        except:
            # 해당 기본 키를 가진 항목을 삭제합니다.
            # key_to_delete = {
            #     'DATE':date,
            #     'TYPE_ID':id
            # }

            # response = table_keyword.delete_item(
            #     Key=key_to_delete
            # )
            print("damn2")

            no_keyword = 1
        ###

        if no_keyword == 1:
            no_keyword = 0
            continue

        sentences = []

        for i, row in df.iterrows():
            remove_sentences = []
            sentence = split_korean_sentences(row['content'])
            for idx in range(len(sentence)):
                if sentence[idx] == "" or len(sentence[idx]) > 190:
                    remove_sentences.append(sentence[idx])

            if len(remove_sentences):
                for remove_sentence in remove_sentences:
                    sentence.remove(remove_sentence)

            sentences.extend(sentence)

        #   sentence.pop()
        #   sentences.extend(sentence)

        data = []

        for sentence in sentences:
            if (sentence == "" or len(sentence) == 0):
                continue
            temp_dict = dict()
            temp_dict['sentence'] = sentence

            # 형태소 분석을 수행합니다.
            morphemes_with_pos = komoran.get_plain_text(sentence)
            morphemes_and_pos = [token.split("/") for token in morphemes_with_pos.split()]

            morphemes_and_pos_idx = 0
            nouns = []
            for word in morphemes_and_pos:
                try:
                    dum = word[1]
                except:
                    morphemes_and_pos.remove(morphemes_and_pos[morphemes_and_pos_idx])

                try:
                    if len(word[1]) > 1 and word[1].startswith("N"):
                        nouns.append(word[0])
                except:
                    morphemes_and_pos.remove(morphemes_and_pos[morphemes_and_pos_idx])
                morphemes_and_pos_idx += 1

            temp_dict['token_list'] = nouns  # 형태소 나누기

            if len(data) == 0:
                data.append(temp_dict)
            for i in range(len(data)):
                stand_len = len(data[i]['token_list']) if len(data[i]['token_list']) < len(
                    temp_dict['token_list']) else len(temp_dict['token_list'])

                inter_len = len(set(data[i]['token_list']) & set(temp_dict['token_list']))

                if stand_len == 0:
                    continue

                if (inter_len / stand_len) >= 0.7:
                    break
                elif i + 1 == len(data):
                    data.append(temp_dict)

        df_1 = pd.DataFrame(data)
        similarity_matrix = []

        for i, row_i in df_1.iterrows():
            i_row_vec = []
            for j, row_j in df_1.iterrows():
                if i == j:
                    i_row_vec.append(0.0)
                else:
                    intersection = len(set(row_i['token_list']) & set(row_j['token_list']))
                    log_i = math.log(len(set(row_i['token_list'])) + 1) + 1
                    log_j = math.log(len(set(row_j['token_list'])) + 1) + 1
                    try:
                        similarity = intersection / (log_i + log_j)
                    except:
                        similarity = 0.0
                    i_row_vec.append(similarity)
            similarity_matrix.append(i_row_vec)

        # sklean 사용
        weightedGraph = np.array(similarity_matrix)
        try:
            nx_graph = nx.from_numpy_array(weightedGraph)

        except:
            print("damn3")

            no_keyword = 1
        ###

        if no_keyword == 1:
            no_keyword = 0
            continue

        scores = divrank(nx_graph)

        k = 0
        for i, n in enumerate(sorted(scores, key=lambda n: scores[n], reverse=True)):
            k = k + 1
            if k == 5:
                break

            sum_text = sum_text + df_1['sentence'][n] + '^^^'

        dynamodb = boto3.resource('dynamodb')
        table_post = dynamodb.Table('POSTPROCESSING')

        # 테이블에 저장
        with table_post.batch_writer() as batch:
            # batch._flush_amount = 1 # 이거 해야 재귀 오류 안 안뜸
            item = {}
            item['DATE'] = date
            item['KEYWORDS'] = keyword
            item['CONTENT'] = sum_text

            batch.put_item(Item=item)

