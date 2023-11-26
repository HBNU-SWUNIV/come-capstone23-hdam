import json

# 데베
import boto3

# Import Module
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import normalize
import numpy as np

# Import Python Library
from datetime import datetime
import time


def lambda_handler(event, context):
    # TODO implement

    # 이벤트 핸들러 함수의 첫 번째 인자 event에 입력 이벤트가 전달됩니다.
    # event 객체는 JSON 형식의 데이터를 가질 수 있습니다.

    # event 객체에서 input_data 키로 전달된 데이터를 추출
    input_data = event

    if input_data is not None:
        # input_data를 가지고 원하는 작업을 수행

        nouns = input_data['nouns']
        words_graph, idx2word = buildWordsGraph(nouns)

        # NumPy 배열을 리스트로 변환
        words_graph = words_graph.tolist()

        input_data['words_graph'] = words_graph
        input_data['idx2word'] = idx2word

        # 결과 데이터를 반환
        return input_data

    else:
        return {
            'error': 'Input data not provided.'
        }


# 단어들간의 유사도 계산
def buildWordsGraph(sentence_noun):
    cnt_vec = CountVectorizer()
    cnt_vec_mat = normalize(cnt_vec.fit_transform(sentence_noun).toarray().astype(float), axis=0)
    vocab = cnt_vec.vocabulary_
    return np.dot(cnt_vec_mat.T, cnt_vec_mat), {vocab[word]: word for word in vocab}