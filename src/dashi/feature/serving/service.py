import asyncio
import orjson

from typing import Dict, List

from dashi import LOGGER
from dashi.feature.serving import *
from dashi.feature.serving.item_feedback_yn_ratio import ItemFeedbackYnRatio
from dashi.feature.serving.item_intro_length import ItemIntroLength
from dashi.feature.serving.item_badge_types import ItemBadgeTypes
from dashi.feature.serving.messages import ItemSearchBasedFeatureEntity


domain_name = "item-reco"


item_feedback_yn_ratio = ItemFeedbackYnRatio(
    service_config=service_config,
    request_session=request_session,
    domain_name=domain_name,
    schema_type="item_feedback_yn_ratio"
)
item_intro_length = ItemIntroLength(
    service_config=service_config,
    request_session=request_session
)
item_badge_types = ItemBadgeTypes(
    service_config=service_config,
    request_session=request_session,
    domain_name=domain_name,
    schema_type="item_badge_types"
)


async def serve_item_feedback_yn_ratio(feature_entities: List[ItemSearchBasedFeatureEntity]):
    return [r.model_dump_json() for r in item_feedback_yn_ratio.serve(feature_entities)]

async def serve_item_intro_length(feature_entities: List[ItemSearchBasedFeatureEntity]):
    return [r.model_dump_json() for r in item_intro_length.serve(feature_entities)]

async def serve_item_badge_types(feature_entities: List[ItemSearchBasedFeatureEntity]):
    return [r.model_dump_json() for r in item_badge_types.serve(feature_entities)]


async def aggregate_results(feature_entities, running_loop=None) -> List[Dict]:
    # Optional[List[ItemSearchBasedFeatureEntity]]
    if len(feature_entities) < 1:
        LOGGER.warning(f"{aggregate_results.__name__}: no feature entities")
        return []

    try:
        tasks = [
            asyncio.create_task(serve_item_feedback_yn_ratio(feature_entities)),
            asyncio.create_task(serve_item_intro_length(feature_entities)),
            asyncio.create_task(serve_item_badge_types(feature_entities)),
        ]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        LOGGER.info(f"{aggregate_results.__name__}: gather {len(results_list)} items through whole features for recommendation_sid: {feature_entities[0].recommendation_sid}")

        entities = []
        for results in zip(*results_list):
            # ItemServingBasedFeatureEntity
            entity = dict()
            for result in results:
                entity.update(orjson.loads(result))
            entities.append(entity)

        return entities
    except Exception as e:
        LOGGER.error(f"{aggregate_results.__name__}: while feature aggregation results, occured error for recommendation_sid: {feature_entities[0].recommendation_sid}, {str(e)}")

