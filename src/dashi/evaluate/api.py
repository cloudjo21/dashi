import json
import socket
from pydantic import BaseModel

from fastapi import APIRouter
from fastapi.responses import FileResponse

from tunip.env import NAUTS_LOCAL_ROOT
from tunip.file_utils import services as file_services
from tunip.service_config import get_service_config

from dashi.evaluate.serve.eval_service import CollectionEvalService
from dashi.utils.deploys import MultiEvalServiceDeploy


api  = APIRouter()

service_config = get_service_config()

file_handler = file_services.get(
    "LOCAL", config=service_config.config
)
snapshot_paths = file_handler.list_dir(service_config.deploy_root_path)
assert snapshot_paths
latest_deploy_path = snapshot_paths[-1]

eval_deploy_json = json.load(open(f"{latest_deploy_path}/deploys/evaluate/eval_deploy.json"))
eval_service_deploy = MultiEvalServiceDeploy.parse_obj(eval_deploy_json)

coll_eval_service = CollectionEvalService(eval_service_deploy)

class EvalItemRequest(BaseModel):
    domain_name: str
    task_name: str
    eval_item: str
    label: str = None
    
@api.post("/eval/")
def eval_result(req: EvalItemRequest):
    
    file_path = coll_eval_service.search(
        req.domain_name,
        req.task_name,
        req.eval_item, 
        req.label
    )
    return FileResponse(file_path)



