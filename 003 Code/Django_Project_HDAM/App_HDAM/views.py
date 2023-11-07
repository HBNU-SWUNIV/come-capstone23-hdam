from django.shortcuts import render
from django.core.paginator import Paginator
import os

# TO SEE THE DATE
from datetime import datetime, timedelta

# TO USE DYNAMODB
import boto3
from boto3.dynamodb.conditions import Key

# TO USE WORDCLOUD
from wordcloud import WordCloud
import matplotlib
matplotlib.use('Agg')  # 백엔드를 'Agg'로 설정하여 GUI를 사용하지 않도록 함
import matplotlib.figure as fig
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# ============================================================================================
# DynamoDB 연동 (EC2에 IAM 역할 추가로)
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

    # 워드 클라우드를 생성해주는 함수 호출. Parameter = date, wordcloud_dict
    if len(wordcloud_dict) > 0:
        generate_wordcloud(wordcloud_dict, date)
    else:
        print("워드 클라우드 미생성")

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

# 키워드에 대한 요약문과, 그 요약문에 관련된 기사를 보여주는 페이지
def main_information(request, date, keyword):
    selected_keywords = keyword.split('&') # 미국&중국을, 리스트 형태로 ["미국","중국"] 이런 형식으로 만들어주기

    # DynamoDB에서 테이블 가져오기 위해 생성한 임시변수
    if len(selected_keywords) >= 2:  # 복합 키워드의 경우, 단일 키워드의 경우 구분
        temp_keywords_val = '&'.join(selected_keywords)  # "미국&중국" 형태로 만들어주기
    else:
        temp_keywords_val = selected_keywords[0]  # ['금리']를 금리로 변환

    # 요약문 관련 부분 정보 가져오기
    # DynamoDB의 POSTPROECSSING 테이블 가져오기
    table_postprocessing = dynamodb.Table('POSTPROCESSING')

    # POSTPROCESSING 테이블에서 후처리 결과물 가져오기
    response_postprocessing = table_postprocessing.query(
        KeyConditionExpression=Key('DATE').eq(date) &
                               Key('KEYWORDS').eq(temp_keywords_val)
    )

    # 키워드 관련 기사 부분 정보 가져오기
    if len(selected_keywords) >= 2:  # 복합 키워드의 경우
        # DynamoDB의 PREPROCESSING 테이블 가져오기
        table_preprocessing = dynamodb.Table('PREPROCESSING')

        # PREPROCESSING 테이블에서 전처리 결과물 가져오기
        response_preprocessing = table_preprocessing.query(
            KeyConditionExpression=Key('DATE').eq(date) &
                                   Key('KEYWORDS').begins_with(temp_keywords_val)
        )
        # 해당 요약문을 생성하게된, 전처리된 데이터
        img_content = response_preprocessing['Items']

    else:  # 단일 키워드의 경우 (전처리 과정 거치지 않음)

        # DynamoDB의 date 테이블 가져오기
        table_crawling = dynamodb.Table(date)

        # 날짜 테이블에서 크롤링 결과물 가져오기
        response_crawling = table_crawling.query(
            KeyConditionExpression=Key('KEYWORD').eq(temp_keywords_val)
        )

        # 해당 요약문을 생성하게된, 크롤링 데이터
        img_content = response_crawling['Items']

    # 해당하는 키워드에 대한 정보가 존재하지 않을때, 에러 페이지로 이동하게 된다.
    # 어느 부분이 비어있는지 확인 위해 if 문 3개로 분류
    if len(response_postprocessing['Items']) == 0 and len(img_content) == 0:
        context = {'error_message': '선택하신 키워드 "' + temp_keywords_val + '" 에 대한 정보가 존재하지 않습니다.'}
        return render(request, 'Main/error.html', context)
    # 관련기사가 존재하지 않을때, 에러 페이지로 이동하게 된다.
    elif len(img_content) == 0:
        context = {'error_message': '선택하신 키워드 "' + temp_keywords_val + '" 에 대한 관련 기사가 존재하지 않습니다.'}
        return render(request, 'Main/error.html', context)
    elif len(response_postprocessing['Items']) == 0:
        context = {'error_message': '선택하신 키워드 "' + temp_keywords_val + '" 에 대한 요약문이 존재하지 않습니다.'}
        return render(request, 'Main/error.html', context)

    # 최종 요약문 결과값 (문장과 문장을 ^^^로 구분되어 출력될 것이다.)
    result_postprocessing = response_postprocessing['Items'][0]['CONTENT']
    result_content = result_postprocessing.split('^^^') # 문장들을 리스트로 변환

    # Paginator로 한 페이지에 8(2x4)개만 나오게끔 구현
    # Pagination 공식 문서 : https://docs.djangoproject.com/en/3.2/topics/pagination/
    paginator = Paginator(img_content, 8)  # 페이지당 10개의 항목을 보여주도록 설정합니다.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 웹 화면에 전달할 내용 시각적으로 제공
    context = {
        'date': date,  # Main Page에서 클릭한 날짜 정보
        'keyword' : keyword, # 선택한 키워드에 대한 정보
        'selected_keywords': selected_keywords, # 선택한 키워드를 띄우기 보기위한 정보
        'result_content' : result_content, # 요약문 결과값
        'page_obj': page_obj,  # 페이지 정보 (관련기사)
    }

    return render(request, 'Main/keyword_inf.html', context)

def main_error(request):
    return render(request, 'Main/error.html')