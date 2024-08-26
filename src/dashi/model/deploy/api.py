from fastapi import APIRouter

from dashi.model.deploy import DeployResponse
from dashi.model.deploy.plm import DeployPlmRequest
from dashi.model.deploy.plm import deploy as deploy_plm
from dashi.model.deploy.xgb import DeployRequest as DeployXgbRequest
from dashi.model.deploy.xgb import deploy as deploy_xgb


api = APIRouter()


@api.post("/deploy/model/plm", response_model=DeployResponse)
def deploy_model_plm(request: DeployPlmRequest):
    return deploy_plm(request)


@api.post("/deploy/model/xgb", response_model=DeployResponse)
def deploy_model_xgb(request: DeployXgbRequest):
    return deploy_xgb(request)
