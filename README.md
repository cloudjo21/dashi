# dashi

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

### only start api server for contents count/length
```shell
cd src;
uvicorn dashi.contents.runner:app --host 0.0.0.0 --port 31018
```

#### request prediction to contents count
```shell
curl --location --request POST 'http://localhost:31018/contents' --header 'Content-Type: application/json' --data '{"domain_name": "cosmetic", "stat_type": "count", "keywords":"버츠비"}'
```

#### request prediction to contents length
```shell
curl --location --request POST 'http://localhost:31018/contents' --header 'Content-Type: application/json' --data '{"domain_name": "cosmetic", "stat_type": "length", "keywords":"코디 화장품"}'
```

## start camera UI server

- vue.js 개발환경 세팅

### nodejs/npm 설치

```shell
yum install nodejs
npm install -g @vue/cli
```

### vscode extension 설치

- vetur 설치
- html css support 설치
- Vue 3 Snippets 설치

### dashi 프로젝트 내 ui 개발용 프로젝트 camera 생성

```shell
vue create camera
```

### camera 프로젝트 이동 후 개발용 ui서버 실행

```shell
npm run serve
```

### vue 내에서 api호출을 위한 axios 설치
```shell
npm install axios
```


```shell
cd camera;
npm run serve
```
