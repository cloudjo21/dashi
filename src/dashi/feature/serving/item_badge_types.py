import pandas as pd
import orjson

from pydantic import BaseModel, ValidationError
from typing import Dict, List, Optional

from tunip.feature_path_utils import (
    DomainBasedFeaturePath,
    SchemaTypedFeaturePath,
    SchemaTypedSnapshotFeaturePath
)
from tunip.path.lake import LakePath
from tunip.snapshot_utils import SnapshotPathProvider
from tunip.time_it import time_it

from dashi import LOGGER
from dashi.feature.serving import SESSION_TIMEOUT
from dashi.feature.serving.messages import ItemSearchBasedFeatureEntity


DEFAULT_HAS_BADGE_TYPE = 0

def has_badge(badge, badge_type):
    if not badge_type:
        return False
    if badge in badge_type:
        return True
    else:
        return False


class ItemInfoFilterClause(BaseModel):
    index_name: str
    item_sids: List[str]

    def apply(self):
        clause = [
            {
                "_index": self.index_name,
                "_id": tid,
                "_source": {
                    "include": [
                        "item_sid",
                        "item_badges"
                    ]
                }
            } for tid in self.item_sids
        ]
        return clause


class QueryBuilder:

    @staticmethod
    def apply(
        item_sids: List[str]
    ):
        item_info_filter_clause = ItemInfoFilterClause(
            index_name="item_info",
            item_sids=item_sids
        )
        clause = {
            "docs": item_info_filter_clause.apply()
        }
        return clause


class SearchDocument(BaseModel):
    item_sid: str

    item_badges: Optional[List[str]] = None

    def has_badge_type(self, badge_type: str) -> int:
        return 1 if has_badge(badge_type, self.item_badges) else DEFAULT_HAS_BADGE_TYPE

    @staticmethod
    def dummy_obj():
        return SearchDocument(
            item_sid="1559758c-41a8-44d0-a039-70c109d1b4cb",
            item_badges=[]
        ).dict()


class ItemBadgeTypesEntity(BaseModel):
    user_account_sid: str

    item_sid: str
    recommendation_sid: str

    BDG100: int
    BDG200: int
    BDG300: int
    BDG400: int


class ItemBadgeTypes:

    def __init__(self, service_config, request_session, domain_name, schema_type):
        self.index_name = "item_info"

        self.service_config = service_config
        self.request_session = request_session

        self.uniq_badge_types = self._initialize(service_config, domain_name, schema_type)

    def _initialize(self, service_config, domain_name, schema_type):
        domain_feature_path = DomainBasedFeaturePath(
            lake_path=LakePath(service_config.username),
            domain_name=domain_name
        )
        schema_info_feature_path = SchemaTypedFeaturePath(
            domain_path=domain_feature_path,
            schema_type=f"{schema_type}.info",
            phase_type="training"
        )
        latest_snapshot_dt = SnapshotPathProvider(service_config).latest_snapshot_dt(
            repr(schema_info_feature_path),
            force_fs=service_config.filesystem.upper()
        )
        schema_snapshot_path = SchemaTypedSnapshotFeaturePath(
            schema_path=schema_info_feature_path,
            snapshot_dt=latest_snapshot_dt
        )

        fs_prefix = service_config.filesystem_prefix

        info_path = f"{fs_prefix}{repr(schema_snapshot_path)}/data.json"

        badge_types = pd.read_json(info_path).loc[:, "badge"].values.tolist()
        return badge_types

    @time_it(LOGGER)
    def serve(self, entities: List[ItemSearchBasedFeatureEntity]) -> List[ItemBadgeTypesEntity]:
        item_sids = [e.item_sid for e in entities]
        query = QueryBuilder.apply(item_sids)
        response = self.request_session.post(
            f"{self.service_config.elastic_host}/_mget",
            # f"{self.service_config.elastic_host}/{self.index_name}/_search",
            data=orjson.dumps(query).decode("utf-8"),
            headers={'Content-Type': 'application/json; charset=utf-8'},
            timeout=SESSION_TIMEOUT
        )
        query_result = response.json()
        search_result = query_result["docs"]

        LOGGER.info(f"{__class__.__name__}: search {len(search_result)} items from {self.index_name}")

        first_entity = entities[0]
        user_account_sid = first_entity.user_account_sid
        recommendation_sid = first_entity.recommendation_sid

        feature_entities: List[ItemBadgeTypesEntity] = []
        search_ids: List[str] = []
        for i in range(len(search_result)):
            source = search_result[i]["_source"]
            try:
                document = SearchDocument.model_validate(source)
            except ValidationError as ve:
                LOGGER.error(f"{__class__.__name__} {source} {ve}")
                raise ve
                # raise ValidationError(f"{__class__.__name__} {source}")

            feature_entity: ItemBadgeTypesEntity = ItemBadgeTypesEntity(
                item_sid=document.item_sid,
                user_account_sid=user_account_sid,
                recommendation_sid=recommendation_sid,
                BDG100=document.has_badge_type("BDG100"),
                BDG200=document.has_badge_type("BDG200"),
                BDG300=document.has_badge_type("BDG300"),
                BDG400=document.has_badge_type("BDG400")
            )
            feature_entities.append(feature_entity)
            search_ids.append(document.item_sid)

        sort_entities = []
        for tid in item_sids:
            if tid in search_ids:
                entity = feature_entities[search_ids.index(tid)] 
            else:
                entity = ItemBadgeTypesEntity(
                    item_sid=tid,
                    user_account_sid=user_account_sid,
                    recommendation_sid=recommendation_sid,
                    BDG100=0,
                    BDG200=0,
                    BDG300=0,
                    BDG400=0
                )
                LOGGER.warning(f"[{__class__.__name__}]: item_sid={tid} IS NOT EXISTING in search-index={self.index_name}")
            sort_entities.append(entity)
        check, lost_items = self.validate_search_response(item_sids, sort_entities, search_ids)
        if check is False:
            LOGGER.warning(f"[{__class__.__name__}]: lost some items in search-index={self.index_name}, item_sids=[{','.join(lost_items)}]")
        return sort_entities


    def validate_search_response(
        self,
        item_sids: List[str],
        search_documents: List[Dict],
        search_ids: List[str]
    ) -> tuple[bool, Optional[List[str]]]:
        check = True
        lost_item_sids = None
        if len(item_sids) == len(search_documents):
            for t, s in zip(item_sids, search_documents):
                if t != s.item_sid:
                    check = False
                    break
        else:
            lost_item_sids = []
            for tid in item_sids:
                if tid not in search_ids:
                    lost_item_sids.append(tid)
            check = False

        return check, lost_item_sids
        
