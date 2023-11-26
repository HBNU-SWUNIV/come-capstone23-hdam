from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import normalize
import numpy as np

#단어들간의 유사도 계산
def buildWordsGraph(sentence_noun):
    cnt_vec = CountVectorizer()
    cnt_vec_mat = normalize(cnt_vec.fit_transform(sentence_noun).toarray().astype(float), axis=0)
    vocab = cnt_vec.vocabulary_
    return np.dot(cnt_vec_mat.T, cnt_vec_mat), {vocab[word] : word for word in vocab}