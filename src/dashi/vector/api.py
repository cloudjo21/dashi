import json
import numpy as np
import os
import requests
import socket
import sys

from fastapi import APIRouter
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional

from tunip.env import NAUTS_LOCAL_ROOT
from tunip.file_utils import services as file_services
from tunip.service_config import get_service_config

from dashi import LOGGER
from dashi.utils.deploys import MultiVectorSetTaskServiceDeploy
from dashi.vector import DomainCollectionInfo
from dashi.vector.serve.vector_index_service import VectorIndexCollectionService


api = APIRouter()


class VecSearchRequest(BaseModel):
    domain_name: str
    task_name: str
    texts: List[str]


class VecSearchResponse(BaseModel):
    item_ids: List[List[int]]
    status: str
    search_results: Optional[List[List[str]]]


# TODO read domains DB for one given domain name
# TODO or get domain ids from domain_partitioner

service_config = get_service_config()
print(service_config.config.dict)
print(service_config.deploy_root_path)
file_handler = file_services.get(
    "LOCAL", config=service_config.config
)
snapshot_paths = file_handler.list_dir(service_config.deploy_root_path)
assert snapshot_paths
latest_deploy_path = snapshot_paths[-1]

vector_deploy_json = json.load(open(f"{latest_deploy_path}/deploys/vector/deploy.json"))
vector_service_deploy = MultiVectorSetTaskServiceDeploy.model_validate(vector_deploy_json)

vector_service = VectorIndexCollectionService(service_config, vector_service_deploy)


@api.post("/vector_set/search", response_model=VecSearchResponse)
def post_search(req: VecSearchRequest):

    body = {
        "model_name":"monologg/koelectra-small-v3-discriminator",
        "texts": req.texts
    }
    response = requests.post('http://127.0.0.1:31018/predict/plm/', json.dumps(body))
    plm_res = json.loads(response.content.decode('utf-8'))

    if plm_res["status"] == "OK":
        q_vector = np.mean(np.asarray(plm_res["result"]).astype('float32'), axis=1)
        # LOGGER.info(f"shape of vector from plm: {np.asarray(plm_res['result']).shape}")
        # LOGGER.info(f"vector from plm: {np.asarray(plm_res['result'])[0, :8]}")
        # LOGGER.info(f"query shape: {q_vector.shape}")
        # LOGGER.info(f"query vector: {q_vector[0]}")
    else:
        return VecSearchResponse(item_ids=[], status="INVALID_RESPONSE_BY_PLM")

    vec_index_res = vector_service.search(
        domain=req.domain_name,
        task=req.task_name,
        q_vector=q_vector
    ) 

    return VecSearchResponse(item_ids=vec_index_res.item_ids, search_results=vec_index_res.search_results, status="OK")
