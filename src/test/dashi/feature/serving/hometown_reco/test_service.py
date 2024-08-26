import pytest


from dashi.feature.serving.hometown_reco.service import (
    load_ranking_model,
    load_ranking_model_weights,
    serve_query,
    rank_docs
)
from dashi.domains.item.hometown.entity import (
    HometownItemRecommendationRequest,
)


@pytest.fixture(scope="module")
def item_reco_request_module():
    request = HometownItemRecommendationRequest(
        recommendation_sid="",
        user_account_sid="19fda1ce-a03f-4e6a-9429-f67db7f2bc4e",
        home_dong_code="1168010100",
        requested_tags=["초등과학"],
        specialties=["2"],
        child_age=8
    )
    return request


def test_ranking_items(item_reco_request_module):
    task_name = "hometown-reco"
    domain_name = "hometown-reco-v1"
    model = load_ranking_model(task_name, domain_name)
    feature_weights = load_ranking_model_weights(task_name, domain_name)
    docs = serve_query(item_reco_request_module)
    prediction = rank_docs(docs, model, feature_weights)
    assert prediction is not None
    assert len(prediction) > 0
