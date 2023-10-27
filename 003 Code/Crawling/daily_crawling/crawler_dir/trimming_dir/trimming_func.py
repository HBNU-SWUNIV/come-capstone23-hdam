#커스텀 함수
from crawler_dir import naver_crawler_func as ncf

# 라이브러리 import
import sys, os
# import requests
import re
import pickle, json, glob, time

# sleep_sec은 0.7초로 설정
sleep_sec = 0.7

############### 본문에 필요없는 문장 추출 함수 ###############
def needless_explain(pho_exps, summary_exps, others_exps):
    needless = []

    # 사진 설명 문장
    for j in pho_exps:
        needless.append(j.text)

    # 맨 위에 나오는 요약 문장
    for j in summary_exps:
        needless.append(j.text)

    # 종종 나오는 불필요 문장
    for j in others_exps:
        needless.append(j.text)

    return needless

############### 불필요한 text 삭제 함수 ###############
def del_pho_exp(deltext, text):
    for k in deltext:
        if k in text:
            text = text.replace(k, "")
    return text


############### 전처리 ###############
def trimming_text(press, text):
    # 종종 위의 text가 섞여 있을 수도 있다고 함.
    rare_pattern = """[\n\n\n\n\n// flash 오류를 우회하기 위한 함수 추가\nfunction _flash_removeCallback() {}"""
    text = text.replace(rare_pattern, '')

    text = text.replace('\n', '').replace('\r', '').replace('<br>', '').replace('\t', '').strip()

    # 첫 문장 시작이 [로 시작해서 ]로 끝나는 문장 지우기
    pub_pattern1 = re.compile("^\[[^\]]+(?=\])\]")
    text = pub_pattern1.sub("", text)

    # [[]] 이렇게 되있는 문장이 있어서 한번더 점검
    pub_pattern1_2 = re.compile("^\]")
    text = pub_pattern1_2.sub("", text)

    # 첫 문장 시작이 ▶로 시작해서 html로 끝나는 문장 지우기
    pub_pattern2 = re.compile("▶.+(?=html)html")
    text = pub_pattern2.sub("", text)

    # ~ 기자로 끝남.
    pub_pattern3 = re.compile("[.].{3,6}기자")
    text = pub_pattern3.sub(".", text)

    ########## 불필요한 기호 제거 ##########
    needless_sign1 = re.compile("━━")
    text = needless_sign1.sub("", text)

    needless_sign2 = re.compile("△")
    text = needless_sign2.sub("", text)

    needless_sign3 = re.compile("▲")
    text = needless_sign3.sub("", text)

    needless_sign4 = re.compile("▷")
    text = needless_sign4.sub("", text)

    needless_sign5 = re.compile("▶")
    text = needless_sign5.sub("", text)

    needless_sign6 = re.compile("━")
    text = needless_sign6.sub("", text)

    needless_sign7 = re.compile("\[")
    text = needless_sign7.sub("", text)

    needless_sign7 = re.compile("\]")
    text = needless_sign7.sub("", text)

    ########## 머니투데이 ##########
    moneytoday_pattern1 = re.compile("\[머니투데이 스타트업 미디어 플랫폼 '유니콘팩토리'\]")
    text = moneytoday_pattern1.sub("", text)

    ########## 헤럴드뉴스 ##########

    ########## YTN ##########[머니투데이 스타트업 미디어 플랫폼 '유니콘팩토리']

    # 마지막에 YTN ~ 입니다. 지우기
    ytn_pattern1 = re.compile("※.+")
    text = ytn_pattern1.sub("", text)

    # YTN 당신의 제보가 어쩌구저쩌구 이러쿵 저러쿵
    ytn_pattern2 = re.compile("YTN.+입니다.")
    text = ytn_pattern2.sub("", text)

    # "■ 진행 : 김영수 앵커 출연 : 김광석 한양대 겸임교수* 아래 텍스트는 ~ 인용 시 ["
    ytn_pattern3 = re.compile("■ 진행 : .+인용 시 \[")
    text = ytn_pattern3.sub("", text)

    # "■ 방송 :  "
    ytn_pattern4 = re.compile("■ 방송 : ")
    text = ytn_pattern4.sub("", text)

    # "◐ 김광석>, ◆ 송승현>, ◇ 박귀빈>" 이런 대화 하는 인물
    ytn_pattern5 = re.compile(". .{2,4}.?>")
    text = ytn_pattern5.sub("", text)

    # "▶ 홍기빈 : "이런 대화하는 인물 제거
    ytn_pattern6 = re.compile(". .{2,4}.?:")
    text = ytn_pattern6.sub("", text)

    # "[앵커], [기자]" 이런 대화하는 인물 제거
    ytn_pattern7 = re.compile("\[.{2,4}\]")
    text = ytn_pattern7.sub("", text)

    ########## 뉴스1 ##########

    # "(~뉴스1) ~ 기자 = "이런거 지우기
    new1_pattern1 = re.compile("^\(.+=뉴스1[^=]+(?==)\=")
    text = new1_pattern1.sub("", text)

    # 2023.3.31/뉴스1
    new1_pattern2 = re.compile(".{4}[.].{1,2}[.].{1,2}/뉴스1")
    text = new1_pattern2.sub("", text)

    # ~대표 =
    new1_pattern3 = re.compile(".+대표 = ")
    text = new1_pattern3.sub("", text)

    ########## 파이낸셜 뉴스 ##########

    # 파이내셜 뉴스 마지막에 해쉬태크
    finen_pattern1 = re.compile("\#(?<=\#).+")
    text = finen_pattern1.sub("", text)

    # 【파이낸셜뉴스 베이징=정지우 특파원】([] 아님)
    finen_pattern2 = re.compile(".파이낸셜뉴스.+특파원.")
    text = finen_pattern2.sub("", text)

    ########## 이데일리 ##########
    edaily_pattern1 = re.compile("\[포토\]")
    text = edaily_pattern1.sub("", text)

    # 맨 마지막에 ■일시: ~ 어쩌구 나오는거 있음
    edaily_pattern2 = re.compile("■일시:.+")
    text = edaily_pattern2.sub("", text)

    if press == "매일경제":
        # [OOO 기자] 제거
        pattern_maeil_1 = re.compile("\[.+?기자\]")
        text = pattern_maeil_1.sub("", text)

        # [신짜오 베트남 - 237] 제거 링크 : http://v.daum.net/v/20230318110310744
        pattern_maeil_2 = re.compile("^\[신짜오 베트남 - .+?\]")
        text = pattern_maeil_2.sub("", text)

        # http://v.daum.net/v/20230321170609589 원희룡 국토교통부장관(사진) 제거
        pattern_maeil_3 = re.compile("\(사진\)")
        text = pattern_maeil_3.sub("", text)

        # http://v.daum.net/v/20230320141501517에서, "이메일 뉴스레터 매부리레터에서 더 자세한 이야기 확인할 수 있습니다. 네이버에서 매부리레터를 검색하면 됩니다." 제거
        pattern_maeil_4 = re.compile("이메일 뉴스레터 매부리레터에서 더 자세한 이야기 확인할 수 있습니다. 네이버에서 매부리레터를 검색하면 됩니다.")
        text = pattern_maeil_4.sub("", text)

    elif press == "뉴시스":
        # 뉴시스의 기사들은 다 [서울 = 뉴시스] 박대기기 기자 이런식의 문구가 들어가 있다.

        # 뉴시스 앞에 기사내용 요약 "기사내용 요약 1월 거래량 1108건…신고 기한 남아 더 늘 전망 지난해 1월 거래량도 뛰어넘어…규제완화 영향  강세훈 기자 =" 이런 형식 제거
        pattern_newsis_1 = re.compile("기사내용 요약.+?\[.+?=.?뉴시스\]")
        text = pattern_newsis_1.sub("", text)

        # 기사내용 요약이 없을경우 [서울=뉴시스] 이런 형식 제거
        pattern_newsis_2 = re.compile("\[.+=.?뉴시스\]")
        text = pattern_newsis_2.sub("", text)

        # "강세훈 기자 =" 이런형식 제거
        pattern_newsis_3 = re.compile(".{1,4} 기자.?=")
        text = pattern_newsis_3.sub("", text)

        # ☞공감언론 뉴시스 kangse@newsis.com  제거
        pattern_newsis_4 = re.compile("☞공감언론.+?com")
        text = pattern_newsis_4.sub("", text)

    elif press == "연합뉴스":
        # "(서울=연합뉴스) 서미숙 기자 =" 삭제
        pattern_yna_1 = re.compile("\(.+?연합뉴스\).+?=")
        text = pattern_yna_1.sub("", text)

        # [OOOO 제공] 삭제
        pattern_yna_2 = re.compile("\[.+?제공\]")
        text = pattern_yna_2.sub(".", text)

        # "▶제보는 카톡 okjebo" 제거
        pattern_yna_3 = re.compile("▶제보는 카톡 okjebo")
        text = pattern_yna_3.sub("", text)

        # 이메일 부분 삭제, (아이디가 1자 ~ 12자인) "sms@yna.co.kr
        pattern_yna_4 = re.compile("[.].{3,15}@yna[.]co[.]kr")
        text = pattern_yna_4.sub(".", text)

        # http://v.daum.net/v/20230317112327649 (윤선희 배영경 채새롬 송은경 홍유담 기자) 제거
        pattern_yna_5 = re.compile("[.].?\(.+?기자\)")
        text = pattern_yna_5.sub(".", text)

    elif press == "한국경제":
        # (.space 이후 삭제), ". 김진수 기자 true@hankyung.com ▶ 해외투자 '한경 글로벌마켓'과 함께하세요▶ 한국경제신문과 WSJ, 모바일한경으로 보세요" 삭제 (거의 무조건 들어있음)
        pattern_hankyung_1_1 = re.compile(".+(?<=\.\s)")
        pattern_hankyung_1_1 = pattern_hankyung_1_1.sub("", text)
        pattern_hankyung_1_2 = re.compile(pattern_hankyung_1_1)
        text = pattern_hankyung_1_2.sub("", text)

        # http://v.daum.net/v/20230218130002889에서 <아파트 탐구> 삭제
        pattern_hankyung_2 = re.compile("<아파트 탐구.+\.")
        text = pattern_hankyung_2.sub("", text)

        # 원희룡 국토교통부장관(사진)에서 (사진)삭제 http://v.daum.net/v/20230321153609614
        pattern_hankyung_3 = re.compile("\(사진\)")
        text = pattern_hankyung_3.sub("", text)

    elif press == "KBS":
        # 마지막에 "박대기 기자 (waiting@kbs.co.kr)".... 삭제
        pattern_kbs_1 = re.compile("[.].{3,6}기자.?\(.{3,15}.+?@kbs[.]co[.]kr\)")
        text = pattern_kbs_1.sub(".", text)

        # [KBS 춘천] 이런 기사 삭제 ex)http://v.daum.net/v/20230218220641135
        pattern_kbs_2 = re.compile("\[KBS.+?\]")
        text = pattern_kbs_2.sub("", text)

        # KBS 지역국 삭제
        pattern_kbs_3 = re.compile("KBS 지역국")
        text = pattern_kbs_3.sub("", text)

    elif press == "중앙일보":
        # 마지막 "황의영·김영주 기자 apex@joongang.co.kr" 제거
        pattern_joongang_1 = re.compile("[.].{3,10}기자.+joongang\.co\.kr")
        text = pattern_joongang_1.sub(".", text)

    elif press == "조선일보":
        # https://v.daum.net/v/20230215190126150 관련
        # "7NEWS 뉴스레터 구독하기 ☞https://page.stibee.com/subscriptions/145557" 삭제
        pattern_chosun_1 = re.compile("7NEWS 뉴스레터 구독하기.+?subscriptions/.{1,6}")
        text = pattern_chosun_1.sub("", text)

        # "기사보기" 삭제
        pattern_chosun_2 = re.compile("기사보기")
        text = pattern_chosun_2.sub("", text)

        # http://v.daum.net/v/20230316153025203 "WEEKLY BIZ Newsletter 구독하기 ☞ https://page.stibee.com/subscriptions/146096" 삭제
        pattern_chosun_3 = re.compile("WEEKLY.BIZ Newsletter 구독하기.+")
        text = pattern_chosun_3.sub("", text)

    elif press == "국민일보":
        # "세종=심희정 기자 simcity@kmib.co.kr GoodNews paper ⓒ 국민일보(www.kmib.co.kr), 무단전재 및 수집, 재배포금지" 삭제
        pattern_kmib_1 = re.compile("[.].{2,11}기자.+@kmib.+재배포금지")
        text = pattern_kmib_1.sub(".", text)

    elif press == "아시아경제":
        # [아시아경제 김민영 기자] 삭제
        pattern_asiae_1 = re.compile("\[아시아경제.+?기자\]")
        text = pattern_asiae_1.sub("", text)

        # "김민영 기자 argus@asiae.co.kr" 삭제
        pattern_asiae_2 = re.compile("[.].{3,10}기자.+@asiae.co.kr")
        text = pattern_asiae_2.sub(".", text)

        # 사진=윤동주 기자 제거 https://v.daum.net/v/20230322144316802
        pattern_asiae_3 = re.compile("사진.?=.{3,6}기자")
        text = pattern_asiae_3.sub("", text)

        # https://v.daum.net/v/20230322144316802뒤에 doso7@ 제거
        pattern_asiae_4 = re.compile("[.].{3,15}@")
        text = pattern_asiae_4.sub("", text)
    elif press == "조선비즈":
        pattern_chobiz_1 = re.compile("- Copyright ⓒ 조선비즈 & Chosun.com -")
        text = pattern_chobiz_1.sub("", text)

    else:
        pass

    # 가끔 span 이나 p에 본문이 있는 경우 내용이 전부 짤릴 경우가 있음
    if text == "" or text == " ": text = "a"

    # 띄어쓰기 없애기
    text = text.replace("  ", " ")
    space_del = re.compile("^ ")
    text = space_del.sub("", text)

    return text