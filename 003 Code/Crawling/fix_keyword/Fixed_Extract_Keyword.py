# About Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By  # Search Element
from selenium.webdriver.chrome.service import Service  # Chrome 경로 설정
from selenium.webdriver.chrome.options import Options  # Selenium에 UserAgent, Headless Chrome

# 시간 라이브러리리
import time  # To use time.sleep() (Dynamic Crawling)


# Extract Fixed Keyword (통계청 - 뉴스기반 검색 - 경제 키워드)
def FixedKeywordCrawler():
    keyword_list = list()
    url = 'http://data.kostat.go.kr/social/keyword/index.do'  # 통계정 경제 키워드

    ###
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1280x1696')
    chrome_options.add_argument('--user-data-dir=/tmp/user-data')
    chrome_options.add_argument('--hide-scrollbars')
    chrome_options.add_argument('--enable-logging')
    chrome_options.add_argument('--log-level=0')
    chrome_options.add_argument('--v=99')
    chrome_options.add_argument('--single-process')
    chrome_options.add_argument('--data-path=/tmp/data-path')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--homedir=/tmp')
    chrome_options.add_argument('--disk-cache-dir=/tmp/cache-dir')
    chrome_options.add_argument(
        'user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')

    chrome_options.binary_location = "/opt/python/bin/headless-chromium"
    driver = webdriver.Chrome('/opt/python/bin/chromedriver', chrome_options=chrome_options)
    ###

    driver.get(url)
    time.sleep(0)

    # 상위 키워드 10개만 크롤링
    for i in range(1, 11):
        keyword_elem = driver.find_element(By.XPATH, '//*[@id="text_{}"]'.format(i))
        keyword_list.append(keyword_elem.text)

    driver.quit()

    return keyword_list
