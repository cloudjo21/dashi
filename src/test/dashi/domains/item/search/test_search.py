import urllib.parse
from fastapi.testclient import TestClient

from tunip.path.mart import MartPretrainedModelPath
from tunip.service_config import get_service_config

from tweak.predict.predictor import PredictorConfig
from tweak.predict.predictors import PredictorFactory

from dashi import LOGGER
from dashi.domains.item.runner import app


client = TestClient(app)


def test_search_items():
    response = client.post(
        '/similarity/request-to-item',
        json={
            "sid":"37d6e00a-bf10-4cf2-9e43-66f2ff7d37a8",
        }
    )
    assert response.status_code == 200
    LOGGER.info(response.json())

def test_get_similarity_request_and_item():
    response = client.post(
        "/similarity/request-and-item",
        json={
            "sid":"37d6e00a-bf10-4cf2-9e43-66f2ff7d37a8",
            "item_sid":"11111111-1f3a-152a-12a5-1f90dbf766a8"
        }
    )
    assert response.status_code == 200
    LOGGER.info(response.json())

def test_get_similarity_request_text_items():
    response = client.post(
        "/similarity/request-text/items",
        json={
            "text": "실내놀이 파닉스 해외 대학교 경력 있는 선생님 부탁드립니다.",
            "specialty": 5
        }
    )
    LOGGER.info(response.json())
    assert response.status_code == 200


def test_predict_for_encoder():
    service_config = get_service_config()
    LOGGER.info(service_config.config.dict)
    model_name = "monologg/koelectra-small-v3-discriminator"
    # model_name = 'hyunwoongko/kobart'
    quoted_model_name = urllib.parse.quote(model_name, safe='')
    plm_model_path = str(
            MartPretrainedModelPath(
            user_name=service_config.username,
            model_name=quoted_model_name
        )
    )
    tokenizer_path = plm_model_path + "/vocab"
    pred_config_json = {
        "predict_tokenizer_type": "auto",
        "predict_model_type": "triton",
        "predict_output_type": "last_hidden.mean_pooling",
        "device": "cpu",
        "model_config": {
            "model_path": f"{plm_model_path}",
            # "model_path": f"{plm_model_path}/onnx/encoder",
            "model_name": model_name,
            # "encoder_only": True,
            "remote_host": "0.0.0.0",
            "remote_port": 31016,
            "remote_model_name": "plm"
        },
        "tokenizer_config": {
            "model_path": plm_model_path,
            "path": tokenizer_path,
            "max_length": 128
        }
    }
    pred_config = PredictorConfig.parse_obj(pred_config_json)
    predictor = PredictorFactory.create(pred_config)

    res = predictor.predict(['영어 되시는 베이비시터 만 20세 이상 구합니다.'])
    LOGGER.info(res.shape)
    assert res is not None
