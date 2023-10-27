# 뉴스당 토큰 갯수 저장, max_features 구할 때 사용
import numpy as np

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

