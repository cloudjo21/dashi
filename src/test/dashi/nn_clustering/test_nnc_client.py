import json
import requests
import timeit
import unittest

from tunip.es_utils import init_elastic_client
from tunip.logger import init_logging_handler
from tunip.service_config import get_service_config


class NncClientTest(unittest.TestCase):
    def setUp(self):
        self.logger = init_logging_handler()
        self.req_session = requests.Session()
        self.edge_case_keyword_examples = [
          "에어플로우",
          "그린스토어",
          "갱남",
          "세올",
        ]
        self.query_examples = {
            "content(그린스토어)",
            "content(에어플로우)",
            "contentnugget(갱남)",
            "content(갱남)",
            "content(보수교육감)",
            "content(넷플릭스) AND content(규제)",
            """
(
  (
    (
      (
        (
          (
            (
              title:(*갱남*) OR title:("갱남"~2^3)
            ) OR
            (
              press:(*갱남*) OR press:("갱남"~2)
            ) OR
            (
              content:(갱남*) OR content:("갱남"~2)
            ) OR
            (
              content:(갱남*) OR content:("갱남"~2)
            )
          )
        ) AND (
          date:[20211209 TO *]
        )
      ) AND (
        NOT content:"##empty##"
      )) AND (NOT category:"tventer")) AND (NOT slave:1)) AND (NOT press:"undefined")""",
      """
(
  (
    (
    (
( (
(
title:(에어플로우) OR
title:("에어플로우"~5^3)
) OR
(
press:(에어플로우) OR
press:("에어플로우"~5)
) OR
(
content:(에어플로우*) OR
content:("에어플로우"~5)
) OR
(
content:(에어플로우*) OR
content:("에어플로우"~5)
)
) ) AND  (
date:[20211209 TO *]
)) AND (NOT content:"##empty##")) AND (NOT category:"tventer")
  ) AND (NOT slave:1)
) AND (NOT press:"undefined")"""
        }

    def test_request_nnc(self):
        index_name = "news-2022-v1"
        search_res_size = 50

        es = init_elastic_client(get_service_config())
        es.indices.exists(index_name)

        for query_example in self.query_examples:
            start = timeit.default_timer()
            query = {
                "query": {"query_string": {"query": query_example}},
                "size": search_res_size,
            }
            es_results = es.search(body=query, index=index_name)
            print(f"{len(es_results['hits']['hits'])} number of result searched..")
            print(f"{timeit.default_timer()-start}ms for es search")

            url = "http://0.0.0.0:31018/nnc/hac"
            body = {"es_result": es_results}

            start = timeit.default_timer()
            response = requests.post(
                url,
                json=body,
                headers={"Content-Type": "application/json; charset=utf-8"},
            )
            print(f"{timeit.default_timer()-start}ms for nnc")
            res_obj = json.loads(response.text)
            assert len(res_obj["es_result"]["hits"]["hits"][0]["inner_hits"]) > 0
            # print(json.dumps(res_obj, indent=4))


    def test_request_nnc_for_all_result(self):
        index_name = "news-2022-v1"
        search_res_size = 50

        es = init_elastic_client(get_service_config())
        es.indices.exists(index_name)

        for query_example in self.query_examples:
            start = timeit.default_timer()
            query = {
                "query": {"query_string": {"query": query_example}},
                "size": search_res_size,
            }
            es_results = es.search(body=query, index=index_name)
            print(f"{len(es_results['hits']['hits'])} number of result searched..")
            print(f"{timeit.default_timer()-start}ms for es search")

            url = "http://0.0.0.0:31018/nnc/hac"
            body = {"es_result": es_results, "result_type": "all"}

            start = timeit.default_timer()
            response = requests.post(
                url,
                json=body,
                headers={"Content-Type": "application/json; charset=utf-8"},
            )
            print(f"{timeit.default_timer()-start}ms for nnc")
            res_obj = json.loads(response.text)
            assert len(res_obj["es_result"]["hits"]["hits"][0]["inner_hits"]) > 0
            # print(json.dumps(res_obj, indent=4))


    def test_request_nnc_for_real_search(self):

        news_search_host = 'http://0.0.0.0:3001/api/v1/news/search' 

        for keyword in self.edge_case_keyword_examples:
            start = timeit.default_timer()
            body = {
              "keyword": keyword,
              "cluster": 9,
              "lastId": 50
            }
            res = self.req_session.post(
                url=f"{news_search_host}", json=body,
                headers={'x-custom-wb-api-header': 'API'}
            )
            res_obj = json.loads(res.text)
            if 'body' not in res_obj['data']['list']:
                assert len(res_obj['data']['list']) == 0 and res_obj['data']['count'] > 0
            else:
                print(f"You need to check this keyword is the expected edge case keyword: {keyword}")
                assert True


    def tearDown(self):
      self.req_session.close()
