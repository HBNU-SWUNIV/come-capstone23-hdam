# 한밭대학교 컴퓨터공학과 HDAM팀

**팀 구성**
- 20181622 송재민
- 20181617 박재필
- 20181630 이용경

## <u>HDAM</u> Project Background
- ### 필요성
  - 금리 변동 및 인플레이션 발생으로 저축으로의 자금 축적보다는 여러 재테크 방법을 통해 저축보다는 투자를 선호하는 사람들의 증가하는 추세
  - 현대 사회에서는 무수히 많은 정보들이 쏟아져 나오는데 이를 일일이 확인하고 정리하기엔 많은 시간이 소요되기 때문에 인기있는 내용만을 빠르고 간단하게 요약함의 필요성이 대두
- ### 기존 해결책의 문제점
  - 하루에 일일이 자료를 찾아 요약하는 작업을 반복하기엔 번거로움
  - 단일 키워드에 대한 요약은 쉽게 할 수 있지만 인기 있는 여러 키워드가 모두 포함된 내용의 뉴스기사만을 수집하여 요약하기에 어려움
 
  
## System Design
  - ##### 사용 언어
    <img src="https://img.shields.io/badge/Python-1572B6?style=for-the-badge&logo=Python&logoColor=white"><img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=HTML5&logoColor=white"><img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=CSS3&logoColor=white">
  - ##### 웹 프레임 워크
    <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=Django&logoColor=white"><img src="https://img.shields.io/badge/Bootstrap-7952B3?style=for-the-badge&logo=Bootstrap&logoColor=white">
  - ##### AWS
    <img src="https://img.shields.io/badge/AWS Lambda-FF9900?style=for-the-badge&logo=AWS Lambda&logoColor=white"><img src="https://img.shields.io/badge/AWS EC2-FF9900?style=for-the-badge&logo=Amazon EC2&logoColor=white"><img src="https://img.shields.io/badge/Amazon DynamoDB-4053D6?style=for-the-badge&logo=Amazon DynamoDB&logoColor=white">
  - ##### 배포 과정
    <img src="https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=Ubuntu&logoColor=white"><img src="https://img.shields.io/badge/NGINX-09639?style=for-the-badge&logo=NGINX&logoColor=white">
  ### ▶️ 시스템 구성도
  ![시스템 구성도](https://github.com/HBNU-SWUNIV/come-capstone23-hdam/assets/125301371/1146fc63-aa67-403d-8a51-cb2b81966a29)
  
  ### ▶️ Database
  -  크롤링한 데이터 및 키워드 등의 정보를 DynamoDB에 테이블을 지정하여 저장

      ![데베(크기조정)](https://github.com/HBNU-SWUNIV/come-capstone23-pool/assets/125301371/7f5ecca7-029a-4782-a37c-bda79f3b4984)

  ### ▶️ 키워드 정보 제공
  -  고정 키워드, 일일 키워드, 복합 키워드의 정보를 제공
  
      -  #### [고정 키워드]
    
          높은 신뢰성을 위해, [통계청에서 제공하는 경제 분야 주요 키워드](https://data.kostat.go.kr/social/keyword/index.do)에서 최근 1주일의 인기있는 경제 키워드를 가져오게 됨
  
      -  #### [일일 키워드]
    
          경제 카테고리의 기사들에서 명사를 추출하고 TextRank 알고리즘을 통해 점수를 매겨 높은 점수를 가진 키워드를 뽑아내어 줌
  
      -  #### [복합 키워드]

          고정 키워드와 일일 키워드에서, 연관된 2개 이상의 키워드 조합이 나올 경우, 그것을 복합 키워드로 선정

  ### ▶️ 요약문 관련 기사 정보 제공
  -  선택한 키워드별 뉴스 기사들의 TF-IDF 수치를 기반으로 DBSCAN을 통해서 군집을 형성
  -  형성된 군집 중 선택 키워드들이 모두 포함된 내용이 주된 내용인 군집을 선별
    ![유사도 수치(크기 조정)(](https://github.com/HBNU-SWUNIV/come-capstone23-hdam/assets/125301371/e3d45c11-3ddf-403f-80b7-626c1b2cbeb6)

  ### ▶️ 요약문 제공
  -  군집화된 뉴스 기사들을 다중문서 요약 알고리즘 중 응답시간이 빠르며 성능이 정확도가 가장 높은 TextRank 알고리즘을 사용하여 요약
      
## Case Study
  - Qiaozhu Mei, Jian Guo, and Dragomir Radev. 2010. DivRank: the interplay of prestige and diversity in information networks. In Proceedings of the 16th ACM SIGKDD international conference on Knowledge discovery and data mining (KDD '10). Association for Computing Machinery, New York, NY, USA, 1009–1018. : https://doi.org/10.1145/1835804.1835931
  - Clustering Sentences with Density Peaks for Multi-document Summarization (Zhang et al., NAACL 2015)
  
## Conclusion
 - ### 기대효과
   - 경제 관련 키워드를 사용하여 뉴스들을 검색하고, 검색된 기사들을 크롤링하여 다량의 뉴스 기사를 수집한다. 그리고 이를 요약함에 있어서 여러 검증을 거치며 다중 키워드와 최대로 관련된 기사를 수집하기에, 사용자에게 친화적이며 다중문서를 요약하여 출력하기에 사용자로 하여금 시간 절약에 큰 힘을 실어줄 수 있다. 특히 경제 관련 기사를 위주로 기사를 가져오기에 투자, 부동산, 금융 관련 등 경제 관련 다양한 분야에서 도움을 줄 수 있다

 - ### 요약 모델 비교
   - TextRank와 DivRank는 비 인공지능 기반의 알고리즘이지만 인공지능 모델인 Kobart, T-5에 비해 응답 속도가 빠르고, 예상보다 정확도가 높아 사용하게 되었다. 다만 위 성능의 경우 단일 문서 요약을 측정하였기에 다중 문서 요약 정확도와 다를 수 있지만 상당한 상관관계가 있을것으로 예측한다.
  
    ![모델 비교 그래프](https://github.com/HBNU-SWUNIV/come-capstone23-hdam/assets/125301371/9a7a4ace-f86e-44dd-9669-b2d4a6b4d85c)

 - ### 최종 결과
    ![최종 요약 결과(크기 조절)](https://github.com/HBNU-SWUNIV/come-capstone23-hdam/assets/125301371/0c39252d-4aed-4750-a4c3-fe7d6e3c3ea0)
  
## Project Outcome

