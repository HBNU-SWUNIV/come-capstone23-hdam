import pandas as pd
import numpy as np
from konlpy.tag import Okt
import math
from sklearn.preprocessing import normalize

okt = Okt()

df = pd.read_excel('C:/Users/jpPark/Untitled Folder/40s.xlsx')

df = df.drop(['Unnamed: 0', 'agency', 'url', 'keyword', ], axis = 1)

sentences = []
for i,row in df.iterrows():
  sentence = row['content'].split('다.')
  for idx in range(len(sentence)):
    if sentence[idx] == "":
      continue
    else:
      sentence[idx] = sentence[idx] + "다."

  sentence.pop()
  sentences.extend(sentence)

data = []
for sentence in sentences:
    if(sentence == "" or len(sentence) == 0):
        continue
    temp_dict = dict()
    temp_dict['sentence'] = sentence
    temp_dict['token_list'] = okt.nouns(sentence) #형태소 나누기
    if len(data) == 0:
      data.append(temp_dict)
    for i in range(len(data)):
        stand_len = len(data[i]['token_list']) if len(data[i]['token_list']) < len(temp_dict['token_list']) else len(temp_dict['token_list'])
        inter_len = len(set(data[i]['token_list']) & set(temp_dict['token_list']))
        if (inter_len / stand_len) >= 0.7:
          break
        elif i+1 == len(data):
          data.append(temp_dict)
df_1 = pd.DataFrame(data)
similarity_matrix = []
for i, row_i in df_1.iterrows():
    i_row_vec = []
    for j, row_j in df_1.iterrows():
        if i == j:
            i_row_vec.append(0.0)
        else:
            intersection = len(set(row_i['token_list']) & set(row_j['token_list']))
            log_i = math.log(len(set(row_i['token_list'])))
            log_j = math.log(len(set(row_j['token_list'])))
            similarity = intersection / (log_i + log_j)
            i_row_vec.append(similarity)
    similarity_matrix.append(i_row_vec)
def pagerank(x, df=0.85, max_iter=30):
    assert 0 < df < 1

    # initialize
    A = normalize(x, axis=0, norm='l1')
    R = np.ones(A.shape[0]).reshape(-1,1)
    bias = (1 - df) * np.ones(A.shape[0]).reshape(-1,1)
    # iteration
    for _ in range(max_iter):
        R = df * (A * R) + bias

    return R
weightedGraph = np.array(similarity_matrix)
R = pagerank(weightedGraph) # pagerank를 돌려서 rank matrix 반환
R = R.sum(axis=1)
indexs = R.argsort()[-5:]


for index in sorted(indexs):
    print(df_1['sentence'][index])