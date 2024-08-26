
import os
import shutil
import subprocess

from pydantic import BaseModel, computed_field
from typing import Optional

from tunip.env import NAUTS_LOCAL_ROOT
from tunip.file_utils import services as file_services
from tunip.service_config import get_service_config

from tweak.model.convert.requests import Sklearn2OnnxRequest
from tweak.model.convert.sklearn.xgb import SklearnModelConvertService

from dashi import LOGGER
from dashi.model.deploy import DeployResponse


service_config = get_service_config(force_service_level="prod")
file_service = file_services(service_config)

print(service_config.config.dict)


class DeployRequest(BaseModel):
    dfs_bucket: str
    service_username: str
    service_instance: str
    deploy_snapshot: str
    dfs_username: str
    vm_instance: str

    model_type: str
    device: str

    domain_snapshot: str
    domain_name: str
    task_name: str

    mart_task_name: str
    mart_domain_name: str

    convey_source_service_username: Optional[str]
    convey_target_service_username: Optional[str]

    @computed_field
    @property
    def triton_model_name(self) -> str:
        return f"{self.domain_name}.{self.model_type}"
    

class DeployAlightException(Exception):
    pass

class DeployConvertException(Exception):
    pass

class DeployException(Exception):
    pass


def _alight(deploy_request: DeployRequest):
    target_model_path = f"/user/{deploy_request.dfs_username}/domains/{deploy_request.domain_name}/{deploy_request.domain_snapshot}/model/{deploy_request.task_name}"

    local_domain_model_path = f"{NAUTS_LOCAL_ROOT}{target_model_path}"
    print(local_domain_model_path)
    if os.path.exists(local_domain_model_path) is False:
        os.makedirs(local_domain_model_path)

    model_ubj_path = f"/user/{deploy_request.dfs_username}/mart/models/{deploy_request.mart_task_name}/{deploy_request.mart_domain_name}/{deploy_request.domain_snapshot}/model.ubj"
    schema_path = f"/user/{deploy_request.dfs_username}/mart/schemata/{deploy_request.mart_task_name}/{deploy_request.mart_domain_name}/{deploy_request.domain_snapshot}/feature_name_map.json"

    # model_ubj_path = f"{deploy_request.dfs_bucket}/user/{deploy_request.dfs_username}/mart/models/{deploy_request.mart_task_name}/{deploy_request.mart_domain_name}/{deploy_request.domain_snapshot}/model/{deploy_request.task_name}"
    # schema_path = f"{deploy_request.dfs_bucket}/user/{deploy_request.dfs_username}/mart/schemata/{deploy_request.mart_task_name}/{deploy_request.mart_domain_name}/{deploy_request.domain_snapshot}/model/{deploy_request.task_name}"

    file_service.download(model_ubj_path)
    file_service.download(schema_path)
    print(model_ubj_path)
    print(schema_path)

    shutil.copy(f"{NAUTS_LOCAL_ROOT}/{model_ubj_path}", local_domain_model_path)
    shutil.copy(f"{NAUTS_LOCAL_ROOT}/{schema_path}", local_domain_model_path)


def _convert(deploy_request: DeployRequest):
    target_model_path = f"/user/{deploy_request.dfs_username}/domains/{deploy_request.domain_name}/{deploy_request.domain_snapshot}/model/{deploy_request.task_name}"

    conv_req = Sklearn2OnnxRequest(
        model_type=deploy_request.model_type,
        domain_name=deploy_request.domain_name,
        domain_snapshot=deploy_request.domain_snapshot,
        task_name=deploy_request.task_name,
    )

    model_converter = SklearnModelConvertService(service_config)
    model_converter(conv_req)

    target_onnx_model_path = f"{target_model_path}/onnx"

    file_service.transfer_from_local(f"{NAUTS_LOCAL_ROOT}{target_onnx_model_path}", target_onnx_model_path)
    # subprocess.call(["gsutil", "cp", "-r", f"{NAUTS_LOCAL_ROOT}{target_onnx_model_path}", f"{service_config.filesystem_prefix}{target_model_path}"])
    # subprocess.call(["gsutil", "ls", "-r", f"{service_config.filesystem_prefix}{target_model_path}"])


def deploy(deploy_request: DeployRequest) -> DeployResponse:

    status_code = 200
    model_output_path = None
    error_message = None

    try:

        try:
            _alight(deploy_request)
        except Exception as e:
            raise DeployAlightException(str(e))

        try:
            _convert(deploy_request)
        except Exception as e:
            raise DeployConvertException(str(e))

        try:
            if deploy_request.convey_source_service_username and deploy_request.convey_target_service_username:
                source_model_path = f"/user/{deploy_request.convey_source_service_username}/domains/{deploy_request.domain_name}/{deploy_request.domain_snapshot}/model/{deploy_request.task_name}"
                target_model_path = f"/user/{deploy_request.convey_target_service_username}/domains/{deploy_request.domain_name}/{deploy_request.domain_snapshot}/model/{deploy_request.task_name}"
                file_service.mkdirs(target_model_path)
                file_service.copy_files(source_model_path, target_model_path)

            target_model_path = f"/user/{deploy_request.dfs_username}/domains/{deploy_request.domain_name}/{deploy_request.domain_snapshot}/model/{deploy_request.task_name}"
            target_onnx_model_path = f"{target_model_path}/onnx"

            target_model_filepath = f"{target_onnx_model_path}/model.onnx"
            target_config_filepath = f"{target_onnx_model_path}/config.pbtxt"

            triton_model_repo_dirpath = f"{NAUTS_LOCAL_ROOT}/user/{deploy_request.service_username}/{deploy_request.vm_instance}/{deploy_request.deploy_snapshot}/deploys/triton"

            file_service.copy_file_to_local(target_model_filepath, f"{triton_model_repo_dirpath}/models/{deploy_request.triton_model_name}/1/model.onnx")
            file_service.copy_file_to_local(target_config_filepath, f"{triton_model_repo_dirpath}/models/{deploy_request.triton_model_name}/config.pbtxt")

            # if os.path.exists(f"{triton_model_repo_dirpath}/models/{deploy_request.triton_model_name}/1") is False:
            #     os.makedirs(f"{triton_model_repo_dirpath}/models/{deploy_request.triton_model_name}/1")

            # subprocess.call(["gsutil", "cp", "-r", f"{service_config.filesystem_prefix}{target_model_filepath}", f"{triton_model_repo_dirpath}/models/{deploy_request.triton_model_name}/1/"])
            # subprocess.call(["gsutil", "cp", "-r", f"{service_config.filesystem_prefix}{target_config_filepath}", f"{triton_model_repo_dirpath}/models/{deploy_request.triton_model_name}/config.pbtxt"])

            model_output_path = f"{triton_model_repo_dirpath}/models/{deploy_request.triton_model_name}/1/model.onnx"
        except Exception as e:
            raise DeployException(str(e))
    except Exception as e:
        LOGGER.error(f"{type(e).__name__}")
        status_code = 500
        error_message = str(e)
    finally:
        return DeployResponse(status_code=status_code, model_output_path=model_output_path, error_message=error_message)
