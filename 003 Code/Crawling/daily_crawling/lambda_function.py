import boto3, json

from crawler_dir import naver_crawler_func as ncf


def lambda_handler(event, context):
    # TODO implement
    ncf.naver_crawler()
