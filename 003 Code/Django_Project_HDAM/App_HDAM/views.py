from django.shortcuts import render
from django.shortcuts import redirect
from django.http import JsonResponse
from django.conf import settings
from django.http import HttpResponse
import os

# TO SEE THE DATE
from datetime import datetime, timedelta

# TO USE DYNAMODB
from decouple import config
import boto3
from boto3.dynamodb.conditions import Key

# TO USE WORDCLOUD
from wordcloud import WordCloud
import matplotlib
matplotlib.use('Agg')  # 백엔드를 'Agg'로 설정하여 GUI를 사용하지 않도록 함
import matplotlib.pyplot as plt
import matplotlib.figure as fig
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# 전처리 관련 Library
import pandas as pd
import numpy as np
from konlpy.tag import Okt
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sentence_transformers import SentenceTransformer, models, util
from ko_sentence_transformers.models import KoBertTransformer


# =============================================================================================
# DynamoDB 연동하는 부분 (AWS와 ACCESS하기 위한 정보들은 프로젝트 로컬 디렉토리에 .env로 저장)
def connect_dynamodb():
    dynamodb = boto3.resource('dynamodb',
        region_name = config('AWS_REGION_NAME'),
        aws_access_key_id = config('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key = config('AWS_SECRET_ACCESS_KEY')
    )
    return dynamodb
# 전역 변수로 dynamoDB와 연결.
# 매번 다른 함수일때마다, DynamoDB를 연결 시켜 줄 필요는 없다.
dynamodb = connect_dynamodb()

# =============================================================================================
# 7일 전부터 어제까지의 날짜를 가져오는 부분
def get_Date():
    # 요일까지 보여주는 코드는 우선 주석처리
    # day_of_week_KR = {
    #     'Monday': '월',
    #     'Tuesday': '화',
    #     'Wednesday': '수',
    #     'Thursday': '목',
    #     'Friday': '금',
    #     'Saturday': '토',
    #     'Sunday': '일'
    # }

    day_list = list()
    current_date = datetime.now()

    for i in range(1,8):
        date_inf = current_date - timedelta(days=i)
        date = date_inf.strftime('%Y-%m-%d')

        # 요일까지 보여주는 코드 (주석 처리)
        # day_of_week = date_inf.strftime('%A')
        # date += day_of_week_KR[day_of_week]
        day_list.append(date)

    return day_list
# =============================================================================================
# WordCloud Generator
# 여러 일자의 워드클라우드를 보여주어야 하기때문에 media에 저장하는 형식으로
def generate_wordcloud(data, date):
    wordcloud_name = str(date) + ".png"
    wordcloud_save_path = 'media/wordcloud/' + str(wordcloud_name)

    # 이미지 파일이 이미 존재하는지 확인. 존재할 시 워드 클라우드를 생성하지 않음
    if os.path.exists(wordcloud_save_path):
        return wordcloud_save_path

    figure = fig.Figure(figsize=(8, 4))  # Figure를 직접 생성
    canvas = FigureCanvas(figure)  # FigureCanvas 객체 생성
    ax = figure.add_subplot(111)  # Axes 객체 추가

    # 워드클라우드 생성 및 그림 그리기
    font_path = 'static/fonts/NanumSquareNeo-cBd.ttf'
    wordcloud = WordCloud(width=1000,
                          height=1000,
                          background_color='white',
                          font_path=font_path,
                          max_words=20,
                          max_font_size=300).generate_from_frequencies(data)
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')

    # 이미지 파일로 저장
    canvas.print_png(wordcloud_save_path)

    return wordcloud_save_path

# # =============================================================================================
# # 전처리 관련 코드
#
# #엑셀 파일 주소
# path = "C:/Users/yg/Desktop/CapstoneDesign_dummy/"
# data = pd.read_excel(path + '네이버_경제뉴스_3000개_물가_금리_정책_2023_05_30.xlsx')
#
# # 전처리의 메인 코드 (우선 더미 데이터를 엑셀 파일로 받아 띄워보기.)
# # news_relation_analysis_func.py
#
# # 엑셀로 사용할때 주석풀기
# def news_relation_analysis(data):
#     # 엑셀파일로 사용시 주석 필요
#     # data = pd.DataFrame(data).T
#     # 기사 내용이 비어있는(NULL 값) 데이터 없애기
#     data = data[data['content'].notnull()]
#
#     # 리스트 형태로 키워드명 가져오기
#     keywords = list(set(data['keyword']))
#
#     # 리스트로 된 키워드들 분리
#     queries = []
#     query = " ".join(keywords)
#     queries.append(query)
#
#     # 기사 본문 토큰화
#     data = tokenization(data)
#
#     # 사용할 tf-idf 값 구하기
#     tfidf_dbscan, tfidf_matrix_dbscan = tf_idf_custom(data['nouns'])
#
#     # DBSCAN 모델 생성, 거리 계산 식으로는 Cosine distance를 이용
#     min_sample = 5
#     dbscan = DBSCAN(eps=0.2, min_samples=min_sample, metric="cosine")
#
#     cluster_label_dbscan = dbscan.fit_predict(tfidf_matrix_dbscan) # 클러스터링 예측값을 데이터 컬럼에 추가(라벨링 작업 : 형성된 군집에 번호를 부여)
#     data['cluster_label_dbscan'] = cluster_label_dbscan # 클러스터링 예측값 데이터 컬럼에 추가
#
#     use_news = 0  # 노이즈가 아닌 군집의 뉴스기사 총 갯수
#
#     # 군집별 기사 갯수(라벨링이 -1, 0은 노이즈로 판별)
#     for i in range(-1, len(set(cluster_label_dbscan)) - 1):
#         if i == -1:  # 노이즈1
#             print("noise -> ", len(data.loc[data['cluster_label_dbscan'] == i]))
#         elif i == 0:  # 노이즈2
#             print("noise2 -> ", len(data.loc[data['cluster_label_dbscan'] == i]))
#         else:  # 군집 형성
#             print("군집 :", i, "->", len(data.loc[data['cluster_label_dbscan'] == i]))
#             use_news += len(data.loc[data['cluster_label_dbscan'] == i])
#
#     print("전체 뉴스 수 :", len(cluster_label_dbscan))
#     print("군집으로 형성된 뉴스개수 :", use_news)
#
#     # ko-sentence-transper을 이용해 키워드와 관련도를 계산하여 특정 점수 이상의 군집만 가져옴
#     use_cluster_labels = []  # 키워드들에 교집합된 cluster_label_dbscan 저장(라벨링 번호들 저장)
#     for i in range(1, len(set(cluster_label_dbscan)) - 1):
#         # 값이 없을경우 있으면 넘어가기
#         if len(data.loc[data['cluster_label_dbscan'] == i]['nouns']) < min_sample: continue
#
#         # ko-sentense 사용, 현재 i(형성된 군집 중 하나)의 유사도 수치구하기
#         print("현재 군집 :", i)
#         mean = ko_sentense_func(data.loc[data['cluster_label_dbscan'] == i]['nouns_join'], queries)
#
#         # 특정 수치의 유사도 수치가 나왔을 때 현재 군집 라벨링번호 저장(n에다가 저장)
#         if mean > 0.4:
#             print("<<<해당 키워드 포함 확인>>>")
#             print("군집 번호 :", i)
#             print("평균 : %.4f" % (mean))
#             use_cluster_labels.append(i)
#             print()
#     print(use_cluster_labels)
#
#     # 불필요 컬럼 삭제
#     data = data.drop(['Unnamed: 0', 'nouns', 'nouns_join'], axis=1)
#     data_list = []
#
#     # 특정 유사도를 가진 군집이 하나 이상이라도 있는 경우 실행
#     if len(use_cluster_labels) != 0:
#         # 저장한 라벨링의 군집들의 데이터를 새로운 데이터프레임 생성
#         for i in use_cluster_labels:
#             data_list.append(data[data['cluster_label_dbscan'] == i])
#         dict_data = pd.concat(data_list, ignore_index=True)
#
#         #엑셀로 저장
#         to_excel(dict_data, len(dict_data))
#
#         #최종적으로 dict_data를 넘겨주기.
#         return dict_data
#     else:
#         return "Fail"
#
#
#
# # 전처리 서브 코드 1-1
# # conetent_tokens_func.py - tokenization
# def tokenization(data):
#     okt = Okt()
#     noun_list = []
#
#     # 각가 기사 본문 토큰화
#     for content in data['content']:
#         nouns = okt.nouns(content)
#         noun_list.append(nouns)
#
#     # 토큰화된 기사 데이터프레임에 추가
#     data['nouns'] = noun_list
#     data['nouns_join'] = [" ".join(noun) for noun in noun_list]
#
#     drop_index_list = []  # 지워버릴 index를 담는 리스트
#     for i, row in data.iterrows():
#         temp_nouns = row['nouns']
#         if len(temp_nouns) == 0:  # 만약 명사리스트가 비어 있다면
#             drop_index_list.append(i)  # 지울 index 추가
#
#         elif len(temp_nouns) < 40:  # 먄약 뉴스기사가 너무 짧거나 영상인 경우
#             drop_index_list.append(i)  # 지울 index 추가
#
#     data = data.drop(drop_index_list)  # 해당 index를 지우기
#
#     # index를 지우면 순회시 index 값이 중간중간 비기 때문에 index를 다시 지정
#     data.index = range(len(data))
#
#     tfidf, tfidf_matrix = tf_idf_custom(data['nouns']) # 토큰화된 본문 tf-idf 수치 계산
#     cosine_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix) # 토큰화된 본문 tfidf 수치로 코사인 유사도 계산
#
#     over_matrix_idx = [] # 중복 본문 제거
#
#     # 0.95 이상의 코사인 수치(중복 본문)인 인덱스 추출
#     for i in cosine_matrix:
#         over_matrix = np.where(i > 0.97)[0]
#         if len(over_matrix) > 1:
#             for j in over_matrix[1:]:
#                 over_matrix_idx.append(j)
#
#     # 일정 수치 이상의 기사 제거 후 데이터프레임에 저장
#     over_matrix_idx = list(sorted(set(over_matrix_idx)))
#     data = data.drop(over_matrix_idx, axis=0)
#     data.index = range(len(data))
#
#     return data
#
# # 전처리 서브 코드 2-1
# # tf_idf_custom_func.py - tf_idf_custom
# def tf_idf_custom(data):
#     # 불영오 모음
#     stopword_path = 'static/stop_word.txt'
#     f_stop_word = open(stopword_path, 'r', encoding='utf-8')
#     stopword_kor = " ".join(f_stop_word.readlines()).split(" ")
#
#     # 최적 max_feature 계산
#     max_feature = max_feature_cal(data)
#
#     # 토큰화된 본문 리스트를 " " 로 join
#     text = [" ".join(noun) for noun in data]
#     # print(text)
#
#     # tfidf 설정
#     tfidf = TfidfVectorizer(stop_words=stopword_kor,
#                             max_features=max_feature,
#                             min_df=3, ngram_range=(1, 5))
#
#     # tfidf 계산
#     tfidf_matrix = tfidf.fit_transform(text).toarray()
#
#     f_stop_word.close()
#
#     return tfidf, tfidf_matrix
#
# # 전처리 서브 코드 2-2
# # tf_idf_custom_func.py - non_word_del
# def non_word_del(all_word, stopword_kor):
#     okt = Okt()
#
#     use_word = []
#
#
#     for i in all_word.keys():
#         # okt는 영어는 그냥 없애버리기 때문에 영어이면 그냥 추가
#         if i.encode().isalpha():
#             use_word.append(i)
#             continue
#
#         i = ''.join(okt.nouns(i))
#
#         if len(i) == 0:
#             continue
#         elif i not in stopword_kor and i.isalpha():
#             use_word.append(i)
#
#     return use_word
#
# # 전처리 서브 코드 3-1
# # clusting_func_dir/get_max_feature_func.py - max_feature_cal
# def max_feature_cal(data):
#     # 뉴스당 토큰 갯수 저장, max_features 구할 때 사용
#
#     noun_word_count = []
#     count = 0
#     idx = []
#     for nouns in data:
#         noun_word_count.append(len(nouns))
#         count += 1
#         idx.append(count)
#     mean = int(np.mean(noun_word_count))
#
#     return mean
#
# # 전처리 서브 코드 4-1
# # get_similarity_func.py - ko_sentense_func
# def ko_sentense_func(data, queries):
#     ##### 유사도 수치 구하는 함수
#
#     # 이밑은 건들 ㄴㄴ
#     word_embedding_model = KoBertTransformer("monologg/kobert", max_seq_length=75)
#     pooling_model = models.Pooling(word_embedding_model.get_word_embedding_dimension(), pooling_mode='mean')
#     model = SentenceTransformer(modules=[word_embedding_model, pooling_model])
#     embedder = SentenceTransformer("jhgan/ko-sbert-sts")
#
#     # ko-sentense-transper을 사용
#     corpus = data.tolist()
#     # content = data['content'].tolist()
#     # title = data['title'].tolist()
#
#     corpus_embeddings = embedder.encode(corpus, convert_to_tensor=True)
#
#     # 키워드와 관련된 수치 구하기
#     for query in queries:
#         query_embedding = embedder.encode(query, convert_to_tensor=True)
#         cos_scores = util.pytorch_cos_sim(query_embedding, corpus_embeddings)[0]
#         cos_scores = cos_scores.cpu()
#         print("현재 키워드 :", query)
#         #
#         #We use np.argpartition, to only partially sort the top_k results
#         top_results = np.argpartition(-cos_scores, range(len(cos_scores)))[:]
#         sum_score = 0
#         for idx in top_results:
#             sum_score += cos_scores[idx]
#             print("(Score: %.4f)" % (cos_scores[idx]))
#             # print(content[idx].strip())
#
#     mean = float(sum_score) / len(cos_scores)
#     # print("평균 : %.4f" %(mean))
#
#     return mean
#
# # 전처리 서브 코드 5-1
# # load_dir/to_exel_func.py - to_excel 엑셀로 전처리된 결과 추출
# def to_excel(extract_dict, len_ext_dict):
#
#     print('데이터프레임 변환\n')
#     ext_df = pd.DataFrame(extract_dict)
#     keywords = list(set(ext_df['keyword']))
#     keyword = " ".join(keywords)
#
#     folder_path = os.getcwd()
#     xlsx_file_name = '{}_선별된 데이터_{}개.xlsx'.format(keyword, len_ext_dict)
#
#     ext_df.to_excel(xlsx_file_name)
#
#     print('엑셀 저장 완료 | 경로 : {}\\{}\n'.format(folder_path, xlsx_file_name))



# =============================================================================================
# 웹 사이트 이동과 관련되어 있는 함수들

# Main Page (처음 들어갔을때 나오는 화면)
def main(request):
    # 일자 가져오기 (최근 일주일 날짜 정보)
    date_context = get_Date()

    # context 변수에 전달할 내용 담기
    context = {
        'date_context': date_context
    }

    # render 하기
    return render(request, 'Main/main.html', context)

# 해당하는 날짜에 대한 정보를 시각화, 해당하는 날짜의 키워드를 가져와야함
def date_view(request, date):
    date_context = get_Date() # 7일 전부터 어제까지의 날짜 ex) 2023-08-28, 2023-08-29 .. 등이 리스트 형태로

    # 선택한 일자가 담겨있는 변수 date를 이용해, 그에 맞는 키워드들을 가져와야 한다. (KEYWORD 테이블에서)
    # DynamoDB에서 KEYWORD 테이블의 키워드들을 가져오기
    table_keyword = dynamodb.Table('KEYWORD')

    # 키워드 가져오기, (Query 사용시, 파티션 키 정렬 키 사용)
    # 고정 키워드 가져오기
    response_fix = table_keyword.query(
        KeyConditionExpression=Key('DATE').eq(date) &
                               Key('TYPE_ID').begins_with('FIX')  # 고정 키워드 인 것
    )
    # 어제 일일 키워드 가져오기
    response_day = table_keyword.query(
        KeyConditionExpression=Key('DATE').eq(date) &
                               Key('TYPE_ID').begins_with('DAY')  # 일일 키워드 인 것
    )

    # 복합 키워드 가져오기
    response_mix = table_keyword.query(
        KeyConditionExpression=Key('DATE').eq(date) &
                               Key('TYPE_ID').begins_with('MIX')  # 복합 키워드 인 것
    )

    # DynamoDB에서 WORDCLOUD 테이블에서 정보 가져오기
    table_worcloud = dynamodb.Table('WORDCLOUD')

    # 워드 클라우드 데이터 가져오기
    response_wordcloud = table_worcloud.query(
        KeyConditionExpression=Key('DATE').eq(date) &
                               Key('DAY_ID').begins_with('DAY') # 워드 클라우드 데이터를 가져오기.
    )
    wordcloud_item = response_wordcloud['Items']

    # 워드클라우드 형태로 만들기 위해, wordcloud_dict 만들기
    wordcloud_dict = dict()
    for item in wordcloud_item:
        keyword_name = item.get('VALUE')
        keyword_count = item.get('COUNT')

        if keyword_name is not None and keyword_count is not None:
            wordcloud_dict[keyword_name] = int(keyword_count)

    print(wordcloud_dict)

    # 워드 클라우드를 생성해주는 함수 호출. Parameter = date, wordcloud_dict
    if len(wordcloud_dict) > 0:
        generate_wordcloud(wordcloud_dict, date)
    else:
        print("No keywords to generate a word cloud.")

    # 워드 클라우드 파일의 위치를 넘겨주기 위해 주소 가져오기
    wordcloud_image_url = f"/media/wordcloud/{date}.png"

    # 변수를 담아 전송
    selected_context= {'date': date} # Select한 날짜의 정보
    # date_context는 이미 ['2023-08-31', ... ] 이런 형식으로 정의되어 있음.

    # 키워드가 아무것도 존재하지 않을때, 에러 페이지로 이동하게 된다.
    if len(response_mix['Items']) == 0 and  len(response_fix['Items']) == 0 and  len(response_day['Items']) == 0:
        context = {'error_message' : '해당하는 날짜에 키워드가 존재하지 않습니다.'}
        return render(request, 'Main/error.html', context)

    # date_inf로 전달할 데이터를 context에 정의
    context = {
        'selected_context': selected_context,
        'date_context': date_context,
        'fix_keyword': response_fix['Items'],
        'day_keyword': response_day['Items'],
        'mix_keyword' : response_mix['Items'],
        'wordcloud_image_url': wordcloud_image_url,
        'wordcloud_dict': wordcloud_dict,
        'date' : date # Main Page에서 클릭한 날짜 정보
    }

    return render(request, 'Main/date_inf.html', context)

# checkbox의 항목을 받아. DynamoDB의 일자에서 해당하는 키워드에 대한 정보를 받아오고, 해당 기사를
def main_summary(request, date):
    # POST 형태로 키워드를 전달 받고, 코드를 실행하여 완성된 요약문을 출력시켜 보여주게 된다.
    if request.method == 'POST':
        # 이전 페이지에서 선택한 키워드를 리스트 형태로 ex) ['한국','일본']
        # 전역 변수 선언으로, img 페이지에서도 볼 수 있도록
        global selected_keywords # [미국], [미국,중국] 형태
        selected_keywords = request.POST.getlist('keyword')[0].split(',') # 반점을 기준으로 split

        # 각각의 키워드에 대한 정보를 받아오게 될 딕셔너리 생성
        news_dict = dict()
        dict_idx = 0

        # # 테이블명은 선택한 날짜로 테이블을 받아와 준다.
        # table_crawles_article = dynamodb.Table(date)
        #
        # # 선택한 키워드에 대한 정보를 하나씩 받아와 news_dict에 저장한다.
        # for selected_keyword in selected_keywords:
        #     # 선택한 키워드에 해당하는 기사 정보 가져오기 (가져와야 할 정보는, keyword, title, thumbnail, url, content)
        #     response_keyword_inf = table_crawles_article.query(
        #         KeyConditionExpression=Key('keyword').eq(selected_keyword) # 해당 키워드와 같은 항목만 가져오게 된다.
        #     )
        #
        #     items = response_keyword_inf['Items'] # 해당하는 키워드와 같은 컬럼의 정보를 가져오게 된다.
        #
        #     # 아마 여러가지 컬럼이 걸렸을 것이다. 그것을 다 news_dict에 담는 작업을 진행해보자.(추후 전처리 과정을 위해)
        #     for item in items:
        #         news_dict[dict_idx] = {
        #             'keyword': item['keyword'],
        #             'title': item['title'],
        #             'thumbnail' : item['thumbnail'],
        #             'url': item['url'],
        #             'content': item['content']
        #         }
        #         dict_idx += 1
        #
        # print(news_dict)

        # 이 다음 keyword_dict를 전처리 코드로 넘겨준다. (아직 코드 미작성)

        # 더미 데이터로 코드 실행시켜보기
        # result = news_relation_analysis(data)

        # 출력된 값 딕셔너리 형태로 만들어주기 (Template에 시각화 하기 위하여)
        # result_dict = dict()
        # for i in range(len(result)):
        #     result_dict[i] = {
        #         'title' : result['title'][i],
        #         'agency' : result['agency'][i],
        #         'url' : result['url'][i],
        #         'content' : result['content'][i]
        #     }

        # 세션으로 다음 페이지로 전달
        # request.session['result_dict'] = result_dict

        # 웹 화면에 전달할 내용 시각적으로 제공
        context = {
            'selected_keywords': selected_keywords, # 선택한 키워드에 대한 정보
            'date': date,  # Main Page에서 클릭한 날짜 정보
            # 'result_dict' : result_dict, # 전처리된 결과물
        }

        return render(request, 'Main/keyword_summary.html', context)

    return redirect('main_sum') # ? 우선

def main_image(request, date):
    # 세션을 통해 result_dict 전달 받기.
    # result_dict = request.session.get('result_dict')
    # if result_dict is not None:
    #     print(result_dict)  # "some value" 출력


    context = {
        'selected_keywords': selected_keywords, # 전역변수 선언
        'date': date,  # Main Page에서 클릭한 날짜 정보
        # 'reuslt_dict' : result_dict
    }

    return render(request, 'Main/keyword_img.html', context)

def main_error(request):
    return render(request, 'Main/error.html')