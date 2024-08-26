import json
import os
import requests

from enum import Enum
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from tunip.file_utils import services as file_services
from tunip.service_config import get_service_config
from tunip.time_it import time_it

from dashi import LOGGER
from dashi.nn_clustering.serve.nnc_service import NncService
from dashi.utils.deploys import NncServiceDeploy


class NNC_RESULT_TYPE(str, Enum):
    docid_only = 'docid_only'
    all = 'all'


class NotSupportedNncResultType(Exception):
    pass


class NncRequest(BaseModel):
    es_result: dict
    result_type: NNC_RESULT_TYPE = NNC_RESULT_TYPE.docid_only


class NncResponse(BaseModel):
    es_result: dict
    # List[List[int]]
    # docid_cluster: list


class SearchAndHacRequest(BaseModel):
    keyword: Optional[str] = None
    reserve_keyword: Optional[str] = None
    offset: int = 0
    result_type: NNC_RESULT_TYPE = NNC_RESULT_TYPE.docid_only


class SearchAndHacResponse(BaseModel):
    es_result: dict


api = APIRouter()


service_config = get_service_config(servers_path=None, force_service_level=os.environ.get('NAUTS_SERVICE_LEVEL'))
NEWS_SEARCH_HOST = service_config.config.get('news.search.host') or '0.0.0.0:30000'

file_handler = file_services.get(
    "LOCAL", config=service_config.config
)
print(f"service_config.deploy_root_path: {service_config.deploy_root_path}")
snapshot_paths = file_handler.list_dir(service_config.deploy_root_path)
print(f"snapshot_paths: {snapshot_paths}")
assert snapshot_paths
latest_deploy_path = snapshot_paths[-1]

nnc_deploy_json = json.load(open(f"{latest_deploy_path}/deploys/nnc/nnc_deploy.json"))
nnc_service_deploy = NncServiceDeploy.parse_obj(nnc_deploy_json)

nnc_service = NncService(nnc_service_deploy)


@api.get("/status/check", response_model=dict)
def healthcheck():
    return {"code": 200}


@api.post("/nnc/hac", response_model=NncResponse)
@timeit(LOGGER)
def hac(req: NncRequest):

    if req.result_type == NNC_RESULT_TYPE.docid_only:
        collapse_result, rest_result = nnc_service.collapse_search_for_docids(
            req.es_result
        )
    elif req.result_type == NNC_RESULT_TYPE.all:
        collapse_result, rest_result = nnc_service.collapse_search(
            req.es_result
        )
    else:
        raise NotSupportedNncResultType(f"Not supported NNC_RESULT_TYPE={req.result_type}")

    es_result = req.es_result
    collapse_result.extend(rest_result)
    es_result['hits']['hits'] = collapse_result

    return NncResponse(es_result=es_result)


@api.post("/nnc/test/search/hac", response_model=SearchAndHacResponse)
@timeit(LOGGER)
def search_and_hac(req: SearchAndHacRequest):

#    reserve_keyword: NEWS_REGU_POLICY
#    query_example = """
#    (
#      (
#          (
#            content:(규제*) OR
#          content:(정책*) OR
#            content:(법안*) OR
#          content:(입법*) OR
#            content:(국정감사*)
#        ) AND (
#          content:(국회*) OR
#            content:(정부*) OR
#          content:(지자체*) OR
#            content:(협회*)
#        ) AND NOT (
#          content:("ETF") OR
#            content:(증시*) OR
#          content:(코스피*) OR
#            content:(코스닥*) OR
#          content:("[포토]") OR
#            content:(수혜주*) OR
#          content:(청약*) OR
#            content:(비규제*) OR
#          title:("[포토]")
#          )
#        )
#    )"""
    es_result = {}
    with requests.Session() as req_session:
        news_search_host = f'http://{NEWS_SEARCH_HOST}/api/v1/news/search' 
        body = {
            "cluster": 9,  # elastic search result by elasticsearch query
            "lastId": req.offset,
            "order": 1  # recent
        }
        if req.keyword:
            body['keyword'] = req.keyword
        if req.reserve_keyword:
            body['reserveKeyword'] = req.reserve_keyword
        res = req_session.post(
            url=f"{news_search_host}", json=body,
            headers={'x-custom-wb-api-header': 'API'}
        )
        es_result = json.loads(res.text)

        if req.result_type == NNC_RESULT_TYPE.docid_only:
            collapse_result, rest_result = nnc_service.collapse_search_for_docids(
                es_result['data']['list']['body']
            )
        elif req.result_type == NNC_RESULT_TYPE.all:
            collapse_result, rest_result = nnc_service.collapse_search(
                es_result['data']['list']['body']
            )
        else:
            raise NotSupportedNncResultType(f"Not supported NNC_RESULT_TYPE={req.result_type}")

        collapse_result.extend(rest_result)
        es_result['data']['list']['body'] = collapse_result

    return SearchAndHacResponse(es_result=es_result['data']['list'])


@api.post("/nnc/test/search", response_model=SearchAndHacResponse)
@timeit(LOGGER)
def search(req: SearchAndHacRequest):
    es_result = {}
    with requests.Session() as req_session:
        news_search_host = f'http://{NEWS_SEARCH_HOST}/api/v1/news/search' 
        body = {
            "cluster": 9,  # elastic search result by elasticsearch query
            "lastId": req.offset,
            "order": 1
        }
        if req.keyword:
            body['keyword'] = req.keyword
        if req.reserve_keyword:
            body['reserveKeyword'] = req.reserve_keyword
        res = req_session.post(
            url=f"{news_search_host}", json=body,
            headers={'x-custom-wb-api-header': 'API'}
        )
        es_result = json.loads(res.text)

        es_body = es_result['data']['list']['body']['hits']['hits']
        ep_list = []
        for e in es_body:
            ep = dict()
            ep['_id'] = e['_id']
            ep_source = dict()
            ep_source['title'] = e['_source']['title']
            if 'titlenugget' in e['_source']:
                ep_source['titlenugget'] = e['_source']['titlenugget']
            else:
                LOGGER.warning(f"there is no titlenugget field of this article: {ep_source['title']}")
            ep['_source'] = ep_source
            ep_list.append(ep)
        es_body = {'hits':{'hits': ep_list}}

    return SearchAndHacResponse(es_result=es_body)
