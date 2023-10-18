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
    dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-2')
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
def main_summary(request, date, keyword):
    global selected_keywords
    selected_keywords = keyword.split('+')

    # 웹 화면에 전달할 내용 시각적으로 제공
    context = {
        'keyword' : keyword, # 선택한 키워드에 대한 정보
        'selected_keywords': selected_keywords, # 선택한 키워드를 띄우기 보기위한 정보
        'date': date,  # Main Page에서 클릭한 날짜 정보
    }

    return render(request, 'Main/keyword_summary.html', context)

def main_image(request, date, keyword):

    # 웹 화면에 전달할 내용 시각적으로 제공
    context = {
        'keyword' : keyword, # 선택한 키워드에 대한 정보
        'selected_keywords': selected_keywords, # 선택한 키워드를 띄우기 보기위한 정보
        'date': date,  # Main Page에서 클릭한 날짜 정보
    }

    return render(request, 'Main/keyword_img.html', context)

def main_error(request):
    return render(request, 'Main/error.html')