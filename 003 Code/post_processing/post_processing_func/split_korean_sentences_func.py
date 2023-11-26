import re


def split_korean_sentences(text):
    # 한글, 영문, 숫자, 특수문자, 공백을 포함한 정규표현식
    pattern = re.compile(r'(.+?(?<!\d)[.!?](?!\d))')
    sentences = pattern.findall(text)
    return sentences
