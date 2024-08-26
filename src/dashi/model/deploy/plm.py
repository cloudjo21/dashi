import os
import subprocess

from pydantic import BaseModel

from tunip.env import NAUTS_LOCAL_ROOT
from tunip.file_utils import services as file_services
from tunip.service_config import get_service_config

from dashi import LOGGER
from dashi.model.deploy import DeployResponse


# *-prod(dev-prod, stage-prod, prod-prod) config (resources/*/.nauts/application.json)
service_config = get_service_config(force_service_level="prod")
file_service = file_services(service_config)

print(service_config.config.dict)


class DeployPlmRequest(BaseModel):
    dfs_bucket: str
    service_username: str
    service_instance: str
    deploy_snapshot: str
    dfs_username: str
    triton_model_name: str
    plm_model_name: str


def deploy(deploy_request: DeployPlmRequest) -> DeployResponse:
    LOGGER.info(f"env.NAUTS_LOCAL_ROOT={NAUTS_LOCAL_ROOT}")

    plm_model_path = f"/user/{deploy_request.service_username}/mart/plm/models/{deploy_request.plm_model_name}"

    model_filepath = f"{plm_model_path}/onnx/encoder/model.onnx"
    config_filepath = f"{plm_model_path}/onnx/encoder/config.pbtxt"
    vocab_dirpath = f"{plm_model_path}/vocab"
    # vocab_filepath = f"{plm_model_path}/vocab/tokenizer.json"

    triton_model_repo_dirpath = f"/user/{deploy_request.service_username}/{deploy_request.service_instance}/{deploy_request.deploy_snapshot}/deploys/triton"
    local_triton_model_path = f"{NAUTS_LOCAL_ROOT}/{triton_model_repo_dirpath}/models/{deploy_request.triton_model_name}"
    local_plm_model_path = f"{NAUTS_LOCAL_ROOT}/user/{deploy_request.service_username}/mart/plm/models/{deploy_request.plm_model_name}"

    status_code = 200
    model_output_path = local_triton_model_path
    error_message = None
    try:

        file_service.copy_file_to_local(model_filepath, f"{local_triton_model_path}/1/model.onnx")
        file_service.copy_file_to_local(config_filepath, f"{local_triton_model_path}/config.pbtxt")
        file_service.transfer_to_local(vocab_dirpath, f"{local_plm_model_path}/vocab")

        # subprocess.call(["gsutil", "cp", "-r", f"{deploy_request.dfs_bucket}{model_filepath}", f"{local_triton_model_path}/1/model.onnx"])
        # subprocess.call(["gsutil", "cp", "-r", f"{deploy_request.dfs_bucket}{config_filepath}", f"{local_triton_model_path}/config.pbtxt"])

        # if os.path.exists(local_plm_model_path) is False:
        #     os.makedirs(local_plm_model_path)
        # subprocess.call(["gsutil", "cp", "-r", f"{deploy_request.dfs_bucket}{vocab_filepath}", local_plm_model_path])
    except Exception as e:
        LOGGER.error(str(e))
        status_code = 500
        model_output_path = None
        error_message = str(e)
    finally:
        return DeployResponse(status_code=status_code, model_output_path=model_output_path, error_message=error_message)
