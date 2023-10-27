import requests
from bs4 import BeautifulSoup
import re

# 기사 url를 받아와 크롤링
def crawlingTitleAndContents(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'}

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    title = soup.head.title.string  # 제목 크롤링

    contents = soup.select_one('#dic_area')  # 기사 내용
    clean_contents = contents.get_text()  # <>태그 있는 기사에서 정리
    clean_contents = re.sub('\xa0|\t|\r|\n|', '', clean_contents)  # 기사에서 불필요한 줄바꿈 같은 것들 삭제

    return title, clean_contents