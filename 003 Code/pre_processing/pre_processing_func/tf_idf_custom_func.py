from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

def tf_idf_custom(data):
    # 불영오 모음
    f_stop_word = open("stop_word.txt", 'r', encoding='utf-8')
    stopword_kor = " ".join(f_stop_word.readlines()).split(" ")

    # 최적 max_feature 계산
    max_feature = max_feature_cal(data)

    # 토큰화된 본문 리스트를 " " 로 join
    text = [" ".join(noun) for noun in data]
    # print(text)

    # tfidf 설정
    tfidf = TfidfVectorizer(stop_words=stopword_kor,
                            max_features=max_feature,
                            min_df=3, ngram_range=(1, 3))

    # tfidf 계산
    tfidf_matrix = tfidf.fit_transform(text).toarray()

    f_stop_word.close()

    return tfidf, tfidf_matrix


def max_feature_cal(data):
    noun_word_count = []
    count = 0
    idx = []
    for nouns in data:
        noun_word_count.append(len(nouns))
        count += 1
        idx.append(count)
    mean = int(np.mean(noun_word_count))

    return mean
