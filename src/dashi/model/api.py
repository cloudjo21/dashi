import json
import socket

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from tunip.env import NAUTS_LOCAL_ROOT
from tunip.file_utils import services as file_services
from tunip.service_config import get_service_config

from dashi.model.serve.model_service import CollectionModelService
from dashi.utils.deploys import MultiTaskServiceDeploy


api = APIRouter()


service_config = get_service_config()
print(service_config.config.dict)
print(service_config.deploy_root_path)
file_handler = file_services.get(
    "LOCAL", config=service_config.config
)
snapshot_paths = file_handler.list_dir(service_config.deploy_root_path)
assert snapshot_paths
latest_deploy_path = snapshot_paths[-1]

model_deploy_json = json.load(open(f"{latest_deploy_path}/deploys/model/model_deploy.json"))
model_service_deploy = MultiTaskServiceDeploy.parse_obj(model_deploy_json)


coll_model_service = CollectionModelService(model_service_deploy)


class PredictRequest(BaseModel):
    domain_name: str
    task_name: str
    texts: List[str]


class PredictResponse(BaseModel):
    result: List[str]
    status: str


@api.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):

    result, status = coll_model_service.search(
        req.domain_name,
        req.task_name,
        req.texts
    )
    result = [json.dumps(r, ensure_ascii=False) for r in result]

    return PredictResponse(result=result, status=status)
