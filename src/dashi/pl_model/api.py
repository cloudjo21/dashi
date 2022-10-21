import json
import socket

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from tunip.env import NAUTS_LOCAL_ROOT
from tunip.file_utils import services as file_services
from tunip.service_config import get_service_config

from dashi.pl_model.serve.pretrained_model_service import PreTrainedModelCollectionService
from dashi.utils.deploys import MultiPretrainingTaskServiceDeploy


api = APIRouter()

service_config = get_service_config()
print(service_config.config.dict)
file_handler = file_services.get(
    "LOCAL", config=service_config.config
)
snapshot_paths = file_handler.list_dir(service_config.deploy_root_path)
assert snapshot_paths
latest_deploy_path = snapshot_paths[-1]

pretrained_model_deploy_json = json.load(open(f"{latest_deploy_path}/deploys/pretrained_model/pretrained_model_deploy.json"))
pretrained_model_service_deploy = MultiPretrainingTaskServiceDeploy.parse_obj(pretrained_model_deploy_json)

model_coll_service = PreTrainedModelCollectionService(pretrained_model_service_deploy)


class PredictRequest(BaseModel):
    model_name: str
    texts: List[str]


class PredictResponse(BaseModel):
    # batch X sentence X token
    result: List[List[List[float]]]
    status: str


@api.post("/predict/plm", response_model=PredictResponse)
def predict(req: PredictRequest):

    result, status = model_coll_service.search(
        req.model_name,
        req.texts
    )

    return PredictResponse(result=result.numpy().tolist(), status=status)
