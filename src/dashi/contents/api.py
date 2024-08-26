import json
import socket

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from tunip.env import NAUTS_LOCAL_ROOT
from tunip.file_utils import services as file_services
from tunip.service_config import get_service_config

from dashi.contents import ValueInfo
from dashi.contents.deploys import MultiContentsTaskServiceDeploy
from dashi.contents.serve.contents_service import ContentsCollectionService


api = APIRouter()

service_config = get_service_config()
print(service_config.config.dict)
file_handler = file_services.get(
    "LOCAL", config=service_config.config
)
snapshot_paths = file_handler.list_dir(service_config.deploy_root_path)
assert snapshot_paths
latest_deploy_path = snapshot_paths[-1]

contents_deploy_json = json.load(open(f"{latest_deploy_path}/deploys/contents/contents_deploy.json"))
print(contents_deploy_json)
contents_service_deploy = MultiContentsTaskServiceDeploy.parse_obj(contents_deploy_json)

contents_service = ContentsCollectionService(service_config, contents_service_deploy)


class ContentsRequest(BaseModel):
    domain_name: str
    stat_type: str
    keywords: str


class ContentsResponse(BaseModel):
    result: List[ValueInfo]
    status: str


@api.post("/contents", response_model=ContentsResponse)
def post_search(req: ContentsRequest):

    result, status = contents_service.search(
        req.domain_name,
        req.stat_type,
        req.keywords
    )

    return ContentsResponse(result=result, status=status)
