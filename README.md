# dashi

## 소개
- ML/추천 관련 서비스를 제공을 목표로 하는 프로젝트
- 벡터 검색, 사전학습/다운스트림 모델 서빙
- online feature store 서빙
- 본 프로젝트에선 되도록 도메인 독립적인 개발을 진행
  - 도메인 종속인 개발은 프로젝트 koshi에서 진행
  - 예를들면, 도메인 데이터 검색 서비스나 도메인과 관련된 추천시스템 서빙 등
- 서비스 상태와 실행관리는 barnacles 프로젝트에서 관리

## 패키지 소개

### vector
- serving vector search service for the domain-task association
- supports two types of vector search index
  - FAISS
  - Elasticsearch
- vector search index is built by vector index builder of the project tweak
- service deploy file
  - vector_deploy.json

### pl_model
- serving the vectors by pre-trained language model from input texts
- supports token-unit vectors from pre-trained language model
- supports the following model runtimes built by the project tweak
  - HF/torchscript/onnx 
- service deploy file
  - pretrained_model_deploy.json

### model
- serving the predictions by downstream-task model of domain-task association from input texts
- service deploy file
  - model_deploy.json

### evaluate
- serving offline-evaluation results of trained model for the domain-task association
- supports downstream task model evaluation results
- model evaluation results are built by the project shellington
- service deploy file
  - eval_deploy.json

### feature
- serving example of feature store
- requires Elasticsearch server

### nn_clustering
- simple serving example of Hierachical Agglomerative Clustering service
- requires the server the project nugget
- service deploy file
  - nnc_deploy.json

## [deployment configuration](deploy.md)

## start all api server

```shell
cd src;
uvicorn dashi.runner:app --host 0.0.0.0 --port 31018
```

### only start api server for model

```shell
cd src;
uvicorn dashi.model.runner:app --host 0.0.0.0 --port 31018
```

#### request prediction to model

```shell
curl --location --request POST 'http://localhost:8889/predict' --header 'Content-Type: application/json' --data '{"domain_name": "wiki_dev", "task_name": "ner", "texts":["안녕하세요. 반가워요"]}'
```

### only start api server for pretrained language model

```shell
cd src;
uvicorn dashi.pl_model.runner:app --host 0.0.0.0 --port 31018
```

#### request prediction to pretrained language model

```shell
curl --location --request POST 'http://localhost:8889/predict/plm' --header 'Content-Type: application/json' --data '{"model_name":"monologg/koelectra-small-v3-discriminator", "texts":["안녕하세요. 반가워요"]}'
```

### only start api server for vector

```shell
cd src;
uvicorn dashi.vector.runner:app --host 0.0.0.0 --port 31018
```

#### request prediction to vector

```shell
curl --location --request POST 'http://localhost:8889/vector_set/search' --header 'Content-Type: application/json' --data '{"domain_name": "wiki.small", "task_name": "entity", "texts":["안녕하세요. 반가워요"]}'
```

