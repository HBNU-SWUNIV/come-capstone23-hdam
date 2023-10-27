from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

import tf_idf_custom_func as ticf


def tokenization(data):
    tfidf, tfidf_matrix = ticf.tf_idf_custom(data['nouns'])  # 토큰화된 본문 tfidf 수치 계산
    cosine_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)  # 토큰화된 본문 tfidf 수치로 코사인 유사도 계산

    over_matrix_idx = []  # 중복 본문 제거

    # 0.95 이상의 코사인 수치(중복 본문)인 인덱스 추출
    for i in cosine_matrix:
        over_matrix = np.where(i > 0.97)[0]
        if len(over_matrix) > 1:
            for j in over_matrix[1:]:
                over_matrix_idx.append(j)

    # 일정 수치 이상의 기사 제거 후 데이터프레임에 저장
    over_matrix_idx = list(sorted(set(over_matrix_idx)))

    return over_matrix_idx

    # data = data.drop(over_matrix_idx, axis=0)
    # data.index = range(len(data))

    # return data
