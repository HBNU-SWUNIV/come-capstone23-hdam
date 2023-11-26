# from sklearn.cluster import DBSCAN
from PyKomoran import *
import pandas as pd
import numpy as np

import json
import math
import time
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key, Attr  # 테이블 읽기기

from concurrent.futures import ThreadPoolExecutor, as_completed


def news_relation_analysis(data, komoran, real_keywords, limit_count):
    # 비어있는 데이터 제거
    data = pd.DataFrame(data).T  # 엑셀로 실행할때 주석걸기
    data = data[data['content'].notnull()]  # Null값 데이터 없애기

    # 키워드명 가져오기
    keywords = list(set(data['keyword']))

    # 리스트로 된 키워드들 분리
    queries = []
    querie = " ".join(keywords)
    queries.append(querie)

    ### Komoran 객체를 생성합니다.
    noun_list = []  # 토큰화 결과

    # 각가 기사 본문 토큰화
    for content in data['content']:
        # 형태소 분석을 수행합니다.
        try:
            morphemes_with_pos = komoran.get_plain_text(content)
        except:
            nouns = ""
            noun_list.append(nouns)
            continue

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

        # 토큰화된 데이터를 리스트에 저장
        noun_list.append(nouns)

    data['nouns'] = noun_list
    data['nouns_join'] = [" ".join(noun) for noun in noun_list]

    drop_index_list = []  # 지워버릴 index를 담는 리스트
    for i, row in data.iterrows():
        temp_nouns = row['nouns']
        if len(temp_nouns) == 0:  # 만약 명사리스트가 비어 있다면
            drop_index_list.append(i)  # 지울 index 추가

        elif len(temp_nouns) < 40:  # 먄약 뉴스기사가 너무 짧거나 영상인 경우
            drop_index_list.append(i)  # 지울 index 추가

    data = data.drop(drop_index_list)  # 해당 index를 지우기

    # index를 지우면 순회시 index 값이 중간중간 비기 때문에 index를 다시 지정
    data.index = range(len(data))
    ###

    nouns_list = []
    for nouns in data['nouns']:
        nouns_list.append(nouns)

    ### TFIDF 및 코사인유사도 측정에 사용될 'dbscan_func' 호출
    target_function_arn = 'arn:aws:lambda:ap-northeast-2:093169469773:function:dbscan_func'  # 호출할 Lambda 함수의 ARN 지정

    # 호출할 함수의 입력 데이터
    input_data = {
        'nouns_list': nouns_list,
        'model': "1"
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
    str_over_matrix_idx = response_payload['nouns_list']  # json형태로 가져와야 해서 list로 저장되어 있음
    ###

    over_matrix_idx = []
    for i in str_over_matrix_idx:
        if not str_over_matrix_idx: break
        over_matrix_idx.append(int(i))

    # 기사 본문 토큰화
    data = data.drop(over_matrix_idx, axis=0)
    data.index = range(len(data))

    # DBSCAN에 쓰일 토큰
    nouns_list = []
    for nouns in data['nouns']:
        nouns_list.append(nouns)

    ### DBSCAN 사용될 'dbscan_func' 호출
    target_function_arn = 'arn:aws:lambda:ap-northeast-2:093169469773:function:dbscan_func'  # 호출할 Lambda 함수의 ARN 지정

    # 호출할 함수의 입력 데이터
    input_data = {
        'nouns_list': nouns_list,
        'model': "2"
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
    str_cluster_label_dbscan = response_payload['nouns_list']  # json형태로 가져와야 해서 list로 저장되어 있음
    ###

    cluster_label_dbscan = []
    for i in str_cluster_label_dbscan:
        cluster_label_dbscan.append(int(i))

    data['cluster_label_dbscan'] = cluster_label_dbscan  # 클러스터링 예측값 데이터 컬럼에 추가

    use_news = 0  # 노이즈가 아닌 군집의 뉴스기사 총 갯수

    # 군집별 기사 갯수(라벨링이 -1, 0은 노이즈로 판별)
    for i in range(-1, len(set(cluster_label_dbscan)) - 1):
        if i == -1:  # 노이즈1
            print("noise -> ", len(data.loc[data['cluster_label_dbscan'] == i]))
        elif i == 0:  # 노이즈2
            print("noise2 -> ", len(data.loc[data['cluster_label_dbscan'] == i]))
        else:  # 군집 형성
            print("군집 :", i, "->", len(data.loc[data['cluster_label_dbscan'] == i]))
            use_news += len(data.loc[data['cluster_label_dbscan'] == i])

    print("전체 뉴스 수 :", len(cluster_label_dbscan))
    print("군집으로 형성된 뉴스개수 :", use_news)

    # DBSCAN에 쓰일 토큰

    # 복합 키워드가 확실히 포함된 클러스터 라벨
    max_content_n = 0
    max_content_label = 0

    # 만약 확실히 포함되지 않을 경우 미흡하더라도 어느정도 비슷한 내용의 클러스터 라벨
    pre_max_content_n = 0
    pre_max_content_label = 0

    # use_cluster_labels = []  # 키워드들에 교집합된 cluster_label_dbscan 저장(라벨링 번호들 저장)
    # 군집별 tf-idf 계산 후 tf-idf 수치 중 높은 순으로 20개의 단어를 추출
    for cls_num in range(1, len(set(cluster_label_dbscan)) - 1):
        # 비어 있으면 넘어가기
        if len(data.loc[data['cluster_label_dbscan'] == cls_num]['nouns']) == 0: continue

        # 하나의 군집의 tf-idf수치 계산
        # cls_tfidf, cls_tfidf_matrix = tf_idf_custom(data.loc[data['cluster_label_dbscan'] == i]['nouns'])
        nouns_list = []
        least_n = 0

        for nouns in data.loc[data['cluster_label_dbscan'] == cls_num]['nouns']:
            nouns_list.append(nouns)
            least_n += 1

        if least_n < 4: continue

        ### DBSCAN 사용
        target_function_arn = 'arn:aws:lambda:ap-northeast-2:093169469773:function:dbscan_func'  # 호출할 Lambda 함수의 ARN 지정

        # 호출할 함수의 입력 데이터
        input_data = {
            'nouns_list': nouns_list,
            'model': "3"
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
        tfidf_voca = response_payload['tfidf_voca']  # json형태로 가져와야 해서 list로 저장되어 있음

        for i, j in zip(tfidf_voca, tfidf_voca.values()):
            tfidf_voca[i] = int(j)

        cls_tfidf_matrix = response_payload['cls_tfidf_matrix']  # json형태로 가져와야 해서 list로 저장되어 있음
        cls_tfidf_matrix = np.array(cls_tfidf_matrix)

        # 하나의 군집의 높은 수치별로 정렬하고 데이터프레임으로 변환 후 상위 20개의 단어사전 저장
        # print("--\n", tfidf_voca, "\n")
        cls_tfidf_df = pd.DataFrame(cls_tfidf_matrix, columns=sorted(tfidf_voca))
        top_20 = cls_tfidf_df.mean().sort_values().index[-20:].tolist()
        # print(top_20)

        # 상위 20개 중 원하는 키워드 포함 시 멈추고 해당 라벨 저장
        top_20_str = ""
        for top_voca in top_20:
            top_20_str = top_20_str + top_voca + " "

        count = 0
        for keyword in keywords:
            if keyword in top_20_str:
                count += 1
                continue

        if count == len(keywords):
            # 군집에 형성된 기사들이 가장 많은 라벨 추출
            if max_content_n < len(data.loc[data['cluster_label_dbscan'] == cls_num]):
                max_content_n = len(data.loc[data['cluster_label_dbscan'] == cls_num])
                max_content_label = cls_num

        elif count == len(keywords) - 1:
            # 군집에 형성된 기사들이 가장 많은 예비 라벨 추출
            if pre_max_content_n < len(data.loc[data['cluster_label_dbscan'] == cls_num]):
                pre_max_content_n = len(data.loc[data['cluster_label_dbscan'] == cls_num])
                pre_max_content_label = cls_num

    if max_content_label:
        use_cluster_label = max_content_label
    else:
        use_cluster_label = pre_max_content_label

    # 불필요 컬럼 삭제 'nouns_join'
    data = data.drop(['nouns_join'], axis=1)

    data_list = []

    # 특정 유사도를 가진 군집이 하나 이상이라도 있는 경우 실행
    if use_cluster_label:
        # 저장한 라벨링의 군집들의 데이터를 새로운 데이터프레임 생성
        data_list.append(data[data['cluster_label_dbscan'] == use_cluster_label])
        dict_data = pd.concat(data_list, ignore_index=True)
        dict_data = dict_data.to_dict('records')

        keywords = "&".join(real_keywords)  # 복합 키워드의 이름과 순서가 같아야하기 때문에 사용

        dynamodb = boto3.resource('dynamodb')

        # 당일 크롤링 한 날짜
        date = str(datetime.now())
        date = date[:date.rfind(' ')]

        ### 복합키워드 저장
        # 복합키워드 저장
        table_keyword = dynamodb.Table('KEYWORD')

        # 테이블에 넣을 항목 정의
        item = {
            'DATE': date,
            'TYPE_ID': 'MIX_{}'.format(limit_count),
            'VALUE': keywords,
            # 여기에 더 많은 속성을 추가할 수 있습니다.
        }

        # 항목을 테이블에 추가
        response = table_keyword.put_item(Item=item)

        table = dynamodb.Table('PREPROCESSING')
        ###

        # 테이블에 저장
        ID = 0
        with table.batch_writer() as batch:
            # batch._flush_amount = 1 # 이거 해야 재귀 오류 안 안뜸
            for i in dict_data:
                item = {}
                item['DATE'] = date
                item['KEYWORDS'] = keywords + "_" + str(ID)
                item['CONTENT'] = i['content']
                item['THUMBNAIL'] = i['thumbnail']
                item['TITLE'] = i['title']
                item['URL'] = i['url']
                item['LABEL'] = i['cluster_label_dbscan']

                batch.put_item(Item=item)

                ID += 1

        return limit_count + 1

    else:
        print("모든 키워드가 포함된 뉴스가 없습니다.")

        return limit_count

