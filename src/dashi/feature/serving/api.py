import asyncio
import time

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from dashi import LOGGER
from dashi.feature.serving.messages import (
    ItemSearchBasedFeatureEntity,
    ItemServingBasedFeatureEntity,
)
from dashi.feature.serving.service import aggregate_results


api = APIRouter()


class ItemRecoFeaturesRequest(BaseModel):
    entities: List[ItemSearchBasedFeatureEntity]


class ItemRecoFeatureResponse(BaseModel):
    entities: List[ItemServingBasedFeatureEntity]
    status_code: int


@api.post("/item-reco/features")
async def get_features(request: ItemRecoFeaturesRequest):

    response = None
    try:
        end = None
        start = time.time()
        entities = await asyncio.wait_for(aggregate_results(request.entities), timeout=3) 
        end = time.time()

        if entities is not None:
            response = ItemRecoFeatureResponse(status_code=200, entities=[ItemServingBasedFeatureEntity.model_validate(e) for e in entities])
        else:
            response = ItemRecoFeatureResponse(status_code=204, entities=None)
    except Exception as e:
        LOGGER.error(f"FEATURE SERVER ERROR for sid:{request.entities[0].recommendation_sid} {str(e)}")
        response = ItemRecoFeatureResponse(status_code=500, entities=None)
    finally:
        if end:
            LOGGER.info(f"{get_features.__name__}: {end-start} secs elapsed.")
        return response
