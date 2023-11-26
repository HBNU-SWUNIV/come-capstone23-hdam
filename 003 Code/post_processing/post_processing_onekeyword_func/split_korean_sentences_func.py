import re


def split_korean_sentences(text):
    # 한글, 영문, 숫자, 특수문자, 공백을 포함한 정규표현식
    pattern1 = re.compile(r'(.+?(?<!\d)[.!?](?!\d))')
    sentences = pattern1.findall(text)

    return sentences
