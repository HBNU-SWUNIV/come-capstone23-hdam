import json

from sklearn.preprocessing import normalize
import numpy as np
import math


def lambda_handler(event, context):
    # TODO implement

    input_data = event

    if input_data is not None:
        weightedGraph = input_data['weightedGraph']
        # 하나의 군집의 tf-idf수치 계산
        weightedGraph = np.array(weightedGraph)

        try:
            input_data['R'] = pagerank(weightedGraph).tolist()
        except:
            input_data['R'] = 1

        # 결과 데이터를 반환
        return input_data

    else:
        input_data['R'] = 'error : Input data not provided.'
        return input_data


def pagerank(x, df=0.85, max_iter=30):
    assert 0 < df < 1

    # initialize
    A = normalize(x, axis=0, norm='l1')
    R = np.ones(A.shape[0]).reshape(-1, 1)
    bias = (1 - df) * np.ones(A.shape[0]).reshape(-1, 1)
    # iteration
    for _ in range(max_iter):
        R = df * (A * R) + bias

    return R