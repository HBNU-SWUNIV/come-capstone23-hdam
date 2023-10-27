import json

from boto3.dynamodb.conditions import Key, Attr
import boto3

import news_relation_analysis as nraf

def lambda_handler(event, context):
    # TODO implement

    # DynamoDB 클라이언트 생성
    dynamodb = boto3.resource('dynamodb')

    # 테이블 이름
    table = dynamodb.Table('2023-10-13')

    n=0
    news_dict = {}
    response = None
    while True:
        if not response:
            response = table.scan()
        else:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])

        for item in response['Items']:
            news_dict[n] = {'keyword':item['keyword'],
                'title':item['title'],
                'content':item['content']
            }
            n += 1

        if 'LastEvaluatedKey' not in response:
            break  # 모든 페이지를 검색했으면 종료

    a = nraf.news_relation_analysis(news_dict)

    return a
