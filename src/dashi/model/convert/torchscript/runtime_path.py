import urllib.parse

from abc import ABC

from tunip.path.mart import MartPretrainedModelPath, MartPretrainedModelRuntimePath
from tunip.path_utils import ModelPath

from dashi.model.convert.requests import Torch2TorchScriptRequest


class ModelInputAndRuntimeOutputProvider(ABC):
    pass


class RuntimePathProviderFactory:
    @classmethod
    def create(self, convert_model_type, user_name):
        if convert_model_type == 'hf.plm_model':
            return RuntimePathProviderForHfPretrainedModel(user_name)
        elif convert_model_type == 'hf.token_classification_model':
            return RutimePathProviderForHfTokenClassificationModel(user_name)
        else:
            RuntimeError("Not Supported Model Type")


class RuntimePathProviderForHfPretrainedModel(ModelInputAndRuntimeOutputProvider):

    def __init__(self, user_name):
        self.user_name = user_name

    def provide(self, conv_req: Torch2TorchScriptRequest):
        model_path = MartPretrainedModelPath(
            user_name=self.user_name,
            model_name=urllib.parse.quote(conv_req.pt_model_name, safe='')
        )

        runtime_model_path = MartPretrainedModelRuntimePath(
            user_name=self.user_name,
            model_name=urllib.parse.quote(conv_req.pt_model_name, safe=''),
            runtime_type='torchscript'
        )
        return (model_path, runtime_model_path)


class RutimePathProviderForHfTokenClassificationModel(ModelInputAndRuntimeOutputProvider):

    def __init__(self, user_name):
        self.user_name = user_name

    def provide(self, conv_req: Torch2TorchScriptRequest):
        model_path = ModelPath(
            user_name=self.user_name,
            domain_name=conv_req.domain_name,
            snapshot_dt=conv_req.domain_snapshot,
            task_name=conv_req.task_name,
            checkpoint=conv_req.checkpoint
        )

        # TODO TokenClassificationModelRuntimePath
        runtime_model_path = f"{str(model_path)}/torchscript"

        return (model_path, runtime_model_path)
