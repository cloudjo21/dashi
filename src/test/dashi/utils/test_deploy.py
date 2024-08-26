import json
import os
import socket
import unittest

from dashi.contents.deploys import *
from dashi.utils.deploys import *


class DeployTest(unittest.TestCase):

    def setUp(self):
        self.home = os.environ['HOME']
        self.serving_host = socket.gethostname()
        self.serving_dt_snapshot = '220502_000000_000000'
 
    def test_parse_model_deploy(self):
        model_deploy_path = f'{self.home}/temp/user/nauts/{self.serving_host}/{self.serving_dt_snapshot}/deploys/model'
        model_deploy_config = {
            "service_tasks": [
                {
                    "domain": "wiki_dev",
                    "task_name": "ner",
                    # "task_type": "TOKEN_CLASSIFICATION",
                    # "dt_snapshot": "20211020_104537_425173",
                    # "checkpoint": "checkpoint-55200",
                    "predictor_config": {
                        "predict_tokenizer_type": "nugget_auto",
                        "predict_model_type": "auto",
                        "model_config": {
                            "model_path": "/user/nauts/domains/wiki_dev/20211020_104537_425173/model/ner",
                            "task_name": "ner",
                            "task_type": "TOKEN_CLASSIFICATION",
                            "checkpoint": "checkpoint-55200"
                        },
                        "tokenizer_config": {
                            "model_path": "/user/nauts/domains/wiki_dev/20211020_104537_425173/model/ner",
                            "task_name": "ner",
                            "max_length": 128
                        }
                    }
                }
            ] 
        }
        model_deploy = MultiTaskServiceDeploy.parse_obj(model_deploy_config)
        print(model_deploy)
        assert model_deploy

    def test_load_model_service(self):
        json_obj = json.load(open('test/dashi/resources/model_deploy.json'))
        model_deploy = MultiTaskServiceDeploy.parse_obj(json_obj)
        print(model_deploy.json())
        assert model_deploy

    def test_load_pretrained_model_service(self):
        json_obj = json.load(open('test/dashi/resources/pretrained_model_deploy.json'))
        model_deploy = MultiPretrainingTaskServiceDeploy.parse_obj(json_obj)
        print(model_deploy.json())
        assert model_deploy

    def test_parse_vector_set_deploy(self):
        vector_set_deploy_path = f'{self.home}/temp/user/nauts/{self.serving_host}/{self.serving_dt_snapshot}/deploys/vector_set'
        vector_set_deploy_config = {
            "service_tasks": [
                {
                    "domain": "fin_circle",
                    "task_name": "vector_set",
                    "vector_set_type": "DOCUMENT",
                    # "vector_set_type": 0,
                    # "dt_snapshot": "19700101_010100_000000"
                }
            ]
        }

        vector_set_deploy = MultiVectorSetTaskServiceDeploy.parse_obj(vector_set_deploy_config)
        print(vector_set_deploy)
        assert vector_set_deploy

    def test_load_vector_set_service(self):
        pass
    

    def test_composite_service_deploy(self):

        composite_deploy_config = {
            "service_root": [
                {
                    "service_tasks": [
                        {
                            "id": 1,
                            "domain": "fin_circle",
                            "snapshot": "20211221_181733_491729",
                            "task_info": {"name": "document", "source_type": "wiki", "index_type": "PCAR128,IVF32,SQ8"}
                        }
                    ]
                },
                {
                    "service_tasks": [
                        {
                            "domain": "wiki_dev",
                            "task_name": "ner",
                            "predictor_config": {
                                "predict_tokenizer_type": "nugget_auto",
                                "predict_model_type": "auto",
                                "model_config": {
                                    "model_path": "/user/nauts/domains/wiki_dev/20211020_104537_425173/model/ner",
                                    "task_name": "ner",
                                    "task_type": "TOKEN_CLASSIFICATION",
                                    "checkpoint": "checkpoint-55200"
                                },
                                "tokenizer_config": {
                                    "model_path": "/user/nauts/domains/wiki_dev/20211020_104537_425173/model/ner",
                                    "task_name": "ner",
                                    "max_length": 128
                                }
                            }
                        }
                    ]
                }
            ]
        }

        composite_service_deploy = CompositeServiceDeploy.parse_obj(composite_deploy_config)
        assert composite_service_deploy
        print(composite_service_deploy)
