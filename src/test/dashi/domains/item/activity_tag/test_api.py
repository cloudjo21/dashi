import requests
import time
from tunip.np_op_utils import normalized_embeddings
from tweak.predict.predictors import SimplePredictorFactory


req_session = requests.Session()

item_contents_host = "http://localhost:32018"
plm_model_name = "cosmoquester/bart-ko-mini"

contents_domain = "item-contents"

predictor = SimplePredictorFactory.create(
    model_name=plm_model_name,
    plm=True, encoder_only=True,
    max_length=128,
    zero_padding=False,
    predict_output_type="last_hidden.mean_pooling",
    device="cuda"
)

query = "책읽기 보드게임"
item_sid = "11111111-1769-1c3f-1918-13a0d6e5fee4"

query_vector = normalized_embeddings(predictor.predict([query]).to("cpu"))

body = {
    "domain": "item_item_contents_1",
    "query": query,
    "query_vector": query_vector.tolist()[0],
    "item_sids": [item_sid]
}

start = time.time()
res = req_session.post(
    url=f"{item_contents_host}/similarity/item-contents", json=body
)
print("{} elapsed: {:.4f}sec".format("/similarity/item-contents", (time.time() - start)))

print(res.content)
import orjson
print(orjson.loads(res.content))
print(orjson.loads(res.content)["scores"])

req_session.close()
