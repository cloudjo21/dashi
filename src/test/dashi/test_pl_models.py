import json
import os
import socket
import unittest

from tunip.env import NAUTS_LOCAL_ROOT
from tweak.predict.predictors import PredictorFactory
from tweak.predict.toolbox import PredictionToolboxPackerForPreTrainedModel

from dashi.utils.deploys import *
from dashi.utils.deploys import MultiTaskServiceDeploy


class PLModelServiceTest(unittest.TestCase):

    def setUp(self):
        self.serving_host = socket.gethostname()
        self.serving_dt_snapshot = '220502_000000_000000'
    
    def test_predict_pl_model_service(self):

        latest_deploy_path = f'{os.environ["HOME"]}/temp/user/nauts/{self.serving_host}/220502_000000_000000'
        pretrained_model_deploy_json = json.load(open(f"{latest_deploy_path}/deploys/pretrained_model/pretrained_model_deploy.json"))
        pretrained_model_service_deploy = MultiPretrainingTaskServiceDeploy.parse_obj(pretrained_model_deploy_json)

        predictor_config = pretrained_model_service_deploy.service_tasks[0].predictor_config

        pred_toolbox = PredictionToolboxPackerForPreTrainedModel.pack(predictor_config)

        tokenizer = pred_toolbox.tokenizer
        model = pred_toolbox.model

        texts = ['안녕 토크나이저!', "안녕하세요. 반가워요"]
        encoded = tokenizer.tokenize(texts)
        print(encoded)
        assert encoded is not None
