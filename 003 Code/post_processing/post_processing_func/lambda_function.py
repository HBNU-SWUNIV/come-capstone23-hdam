import json

import pandas as pd
import numpy as np
from PyKomoran import *
import math

import time
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key, Attr  # 테이블 읽기기

from split_korean_sentences_func import split_korean_sentences


def lambda_handler(event, context):
    # TODO implement

    komoran = Komoran(DEFAULT_MODEL['FULL'])

    # 테이블명 : 크롤링 한 날짜
    date = str(datetime.now())
    date = date[:date.rfind(' ')]

    # DynamoDB 클라이언트 생성
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('PREPROCESSING')

    n = 0
    news_dict = {}

    # 부동산에 대한 쿼리
    response = table.query(
        KeyConditionExpression=Key('DATE').eq(date)
    )

    items = response['Items']

    # 'LastEvaluatedKey'가 존재하는 경우, 추가 데이터가 더 있음
    while 'LastEvaluatedKey' in response:
        response = table.query(
            KeyConditionExpression=Key('DATE').eq(date),
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        items.extend(response['Items'])

    keywords = []
    for item in items:
        dum_keyword = item['KEYWORDS'].split("_")
        keywords.append(dum_keyword[0])
        news_dict[n] = {
            'keyword': dum_keyword[0],
            'content': item['CONTENT'],
            'cluster_label': item['LABEL']
        }

        n += 1
        # if n == 30: break

    keywords = set(keywords)

    for keyword in keywords:
        print(keyword)
        # 비어있는 데이터 제거
        data = {}
        keyword_n = 0

        for i in news_dict.values():
            if i['keyword'] == keyword:
                data[keyword_n] = i
                keyword_n += 1

                if keyword_n == 20: break

        temp_df = pd.DataFrame(data).T  # 엑셀로 실행할때 주석걸기
        temp_df = temp_df[temp_df['content'].notnull()]  # Null값 데이터 없애기

        res = ""
        for i in temp_df['cluster_label'].unique():
            df = temp_df[temp_df['cluster_label'] == i]
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

                # 빈 리스트 요소 제거
                if len(nouns) == 0:
                    break

                temp_dict['token_list'] = nouns  # 형태소 나누기

                if len(data) == 0:
                    data.append(temp_dict)
                for i in range(len(data)):
                    stand_len = len(data[i]['token_list']) if len(data[i]['token_list']) > len(
                        temp_dict['token_list']) else len(temp_dict['token_list'])

                    inter_len = len(set(data[i]['token_list']) & set(temp_dict['token_list']))

                    if stand_len == 0:
                        continue

                    if (inter_len / stand_len) >= 0.7:
                        break
                    elif i + 1 == len(data):
                        data.append(temp_dict)

            df_1 = pd.DataFrame(data)
            df_1 = df_1[df_1['token_list'].notnull()]
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

            ### DBSCAN 사용
            target_function_arn = 'arn:aws:lambda:ap-northeast-2:093169469773:function:post_sklearn_func'  # 호출할 Lambda 함수의 ARN 지정

            # 호출할 함수의 입력 데이터
            weightedGraph = weightedGraph.tolist()

            input_data = {
                'weightedGraph': weightedGraph,
                'R': 1
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

            # 문자열 리스트만 가져올 수 있어서 문자열로 가져오고 int로 변환
            if response_payload['R'] == 1:
                print("죠졌네 이거")
                return

            R = response_payload['R']  # json형태로 가져와야 해서 list로 저장되어 있음
            R = np.array(R)
            R = R.sum(axis=1)
            indexs = R.argsort()[-5:]

            for index in sorted(indexs):
                res = res + df_1['sentence'][index] + "^^^"

        dynamodb = boto3.resource('dynamodb')
        table_post = dynamodb.Table('POSTPROCESSING')

        # 테이블에 저장
        with table_post.batch_writer() as batch:
            # batch._flush_amount = 1 # 이거 해야 재귀 오류 안 안뜸
            item = {}
            item['DATE'] = date
            item['KEYWORDS'] = keyword
            item['CONTENT'] = res

            batch.put_item(Item=item)
