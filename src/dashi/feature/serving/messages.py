import orjson

from enum import IntEnum
from pydantic import BaseModel, Field, computed_field
from typing import List, Optional

from dashi.feature.serving import ItemFeatureEntity


class ItemRecommendationRequestConfig(BaseModel):
    pass


class ItemSearchBasedFeatureEntity(ItemOnlySearchBasedFeatureEntity, BaseModel):
    user_account_sid: str
    recommendation_sid: str


class ItemServingBasedFeatureEntity(ItemFeatureEntity, BaseModel):
    user_account_sid: str
    recommendation_sid: str

    positive_ratio: float
    intro_len: int
    BDG100: int
    BDG200: int
    BDG300: int
    BDG400: int


class FeatureEntitiesWithSearchResult:
    entities: List[ItemSearchBasedFeatureEntity]
    search_result: dict
