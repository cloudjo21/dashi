import json
import socket
import unittest

from tunip.env import NAUTS_LOCAL_ROOT
from tweak.predict.predictors import PredictorFactory

from dashi.utils.deploys import MultiTaskServiceDeploy


class ModelServiceTest(unittest.TestCase):

    def setUp(self):
        self.serving_host = socket.gethostname()
        self.serving_dt_snapshot = '220502_000000_000000'
    
    def test_init_model_service(self):
        with open('test/dashi/resources/model_deploy.json') as f:
            json_str = json.load(f)
        model_deploy = MultiTaskServiceDeploy.parse_obj(json_str)
        print(model_deploy.json())
        assert model_deploy

        # create specific predictor by task type
        predictor = PredictorFactory.create(model_deploy.service_tasks[0].predictor_config)
        assert predictor

        # model_deploy.domain
        # model_deploy.predictor_config.model_config.model_path
