# from sklearn.cluster import DBSCAN
from PyKomoran import *
import pandas as pd
import numpy as np

# import tf_idf_custom_func as ticf
# import content_tokens_func as ctf

import json
import math
import time
import datetime
import boto3

from concurrent.futures import ThreadPoolExecutor, as_completed


def news_relation_analysis(data):
    # 비어있는 데이터 제거
    data = pd.DataFrame(data).T  # 엑셀로 실행할때 주석걸기
    data = data[data['content'].notnull()]  # Null값 데이터 없애기

    # 키워드명 가져오기
    keywords = list(set(data['keyword']))

    # 리스트로 된 키워드들 분리
    queries = []
    querie = " ".join(keywords)
    queries.append(querie)

    # ###### 멀티스레드 사용
    # with ThreadPoolExecutor(max_workers=8) as executor:
    #     results = executor.submit(ctf.tokenization, content_list)

    #     data = results.result()
    # ######

    ### Komoran 객체를 생성합니다.
    noun_list = []  # 토큰화 결과

    komoran = Komoran(DEFAULT_MODEL['FULL'])

    # 각가 기사 본문 토큰화
    for content in data['content']:
        # 형태소 분석을 수행합니다.
        morphemes_with_pos = komoran.get_plain_text(content)
        morphemes_and_pos = [token.split("/") for token in morphemes_with_pos.split()]

        # 형태소 중에서 명사만 추출합니다.
        try:
            nouns = [word for word, pos in morphemes_and_pos if len(pos) > 1 and pos.startswith("N")]
        except:
            print("dpfkdl")

        noun_list.append(nouns)  # 토큰화된 기사 데이터프레임에 추가

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

    #
    nouns_list = []
    for nouns in data['nouns']:
        nouns_list.append(nouns)

    ### TFIDF 및 코사인 뭐시기 사용
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
    print(str_over_matrix_idx)
    ###

    over_matrix_idx = []
    for i in str_over_matrix_idx:
        if not str_over_matrix_idx: break
        over_matrix_idx.append(int(i))

    # 기사 본문 토큰화
    data = data.drop(over_matrix_idx, axis=0)
    data.index = range(len(data))

    # DBSCAN에 쓰일 토큰큰
    nouns_list = []
    for nouns in data['nouns']:
        nouns_list.append(nouns)

    # # 사용할 tf-idf 값 구하기
    # tfidf_dbscan, tfidf_matrix_dbscan = ticf.tf_idf_custom(data['nouns']) # data['nouns'] 필요요

    # # DBSCAN 모델 생성, 거리 계산 식으로는 Cosine distance를 이용
    # min_sample = 5
    # dbscan = DBSCAN(eps=0.2, min_samples=min_sample, metric="cosine")

    # cluster_label_dbscan = dbscan.fit_predict(tfidf_matrix_dbscan)  # 클러스터링 예측값을 데이터 컬럼에 추가(라벨링 작업 : 형성된 군집에 번호를 부여)

    ### DBSCAN 사용
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

    ### 제목으로 유사도 육안 확인
    count2 = 0
    for cluster_num in set(cluster_label_dbscan):
        # -1,0은 노이즈 판별이 났거나 클러스터링이 안된 경우
        if (cluster_num == -1 or cluster_num == 0):
            continue
        else:
            print("cluster num : {}".format(cluster_num))
            temp_df = data[data['cluster_label_dbscan'] == cluster_num]  # cluster num 별로 조회
            count = 0
            for title, content in zip(temp_df['title'], temp_df['content']):
                print(title)  # 제목으로 살펴보자
                print()
                count += 1
            print()
        count2 += 1
    ###

    # DBSCAN에 쓰일 토큰큰
    nouns_list = []
    for nouns in data.loc[data['cluster_label_dbscan'] == i]['nouns']:
        nouns_list.append(nouns)

    # 군집별 tf-idf 계산 후 tf-idf 수치 중 높은 순으로 20개의 단어를 추출
    for i in range(1, len(set(cluster_label_dbscan)) - 1):
        # 비어 있으면 넘어가기
        if len(data.loc[data['cluster_label_dbscan'] == i]['nouns']) == 0: continue

        # 하나의 군집의 tf-idf수치 계산
        # cls_tfidf, cls_tfidf_matrix = tf_idf_custom(data.loc[data['cluster_label_dbscan'] == i]['nouns'])

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
        print("--\n", tfidf_voca, "\n")
        cls_tfidf_df = pd.DataFrame(cls_tfidf_matrix, columns=sorted(tfidf_voca))
        top_20 = cls_tfidf_df.mean().sort_values().index[-20:].tolist()
        print(top_20)

        # 상위 20개 중 원하는 키워드 포함 시 멈추고 해당 라벨 저장
        top_20_str = ""
        for top_voca in top_20:
            top_20_str = top_20_str + top_voca + " "

        count = 0
        for keyword in keywords:
            if keyword in top_20_str:
                count += 1
                continue
            print(top_20_str)
            print("---------")

        print("--------------------------")
        if count == len(keywords):
            print("<<<해당 키워드 포함 확인>>>")
            print("군집 번호 :", i)
            use_cluster_labels.append(i)
            print("상위 20개의 주요 키워드")
            print(top_20)
            print()

    # 불필요 컬럼 삭제 # 'nouns',
    data = data.drop(['nouns_join'], axis=1)
    data_list = []

    use_cluster_labels = []  # 키워드들에 교집합된 cluster_label_dbscan 저장(라벨링 번호들 저장)
    # 특정 유사도를 가진 군집이 하나 이상이라도 있는 경우 실행
    if len(use_cluster_labels) != 0:
        # 저장한 라벨링의 군집들의 데이터를 새로운 데이터프레임 생성
        for i in use_cluster_labels:
            data_list.append(data[data['cluster_label_dbscan'] == i])
        dict_data = pd.concat(data_list, ignore_index=True)

        # return data_list[0]
        print(data_list[0])

        # 엑셀로 저장
        # tef.to_excel(dict_data, len(dict_data))

        # DB에 저장
        # ldf.load_db(extract_dict)
    else:
        print("모든 키워드가 포함된 뉴스가 없습니다.")
