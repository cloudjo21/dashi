import orjson

from pydantic import BaseModel, ValidationError
from typing import Dict, List, Optional

from tunip.feature_path_utils import (
    DomainBasedFeaturePath,
    SchemaTypedFeaturePath,
    SchemaTypedSnapshotFeaturePath,
)
from tunip.file_utils import services as file_services
from tunip.path.lake import LakePath
from tunip.service_config import ServiceLevelConfig
from tunip.snapshot_utils import SnapshotPathProvider
from tunip.time_it import time_it

from dashi import LOGGER
from dashi.feature.serving import SESSION_TIMEOUT
from dashi.feature.serving.messages import ItemSearchBasedFeatureEntity


class ItemAggrInfoFilterClause(BaseModel):
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
                        "positive_count",
                        "negative_count",
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
        item_aggr_info_filter_clause = ItemAggrInfoFilterClause(
            index_name="item_aggr_info",
            item_sids=item_sids
        )
        clause = {
            "docs": item_aggr_info_filter_clause.apply()
        }
        return clause


class SearchDocument(BaseModel):
    item_sid: str

    positive_count: int = 0
    negative_count: int = 0

    def get_positive_ratio(self, mean_ratio) -> float:
        if self.positive_count > 0:
            return self.positive_count / (self.positive_count + self.negative_count)
        return mean_ratio

    @staticmethod
    def dummy_obj():
        return SearchDocument(
            item_sid="1559758c-41a8-44d0-a039-70c109d1b4cb",
            positive_count=0,
            negative_count=0,
        ).dict()


class ItemFeedbackYnRatioEntity(BaseModel):
    item_sid: str

    user_account_sid: str
    recommendation_sid: str

    positive_ratio: float


class ItemFeedbackYnRatio:

    def __init__(self, service_config, request_session, domain_name, schema_type):
        self.index_name = "item_aggr_info"

        self.service_config = service_config 
        self.request_session = request_session

        self.domain_name = domain_name
        self.schema_type = schema_type

        self.feedback_ratio_info: dict = self._initialize(self.service_config, self.domain_name, self.schema_type)

    def _initialize(self, service_config, domain_name, schema_type):
        file_service = file_services(service_config)

        domain_feature_path = DomainBasedFeaturePath(
            lake_path=LakePath(service_config.username),
            domain_name=domain_name
        )

        info_path = SchemaTypedFeaturePath(
            domain_path=domain_feature_path,
            schema_type=f"{schema_type}.info",
            phase_type="training"
        )
        info_latest_snapshot_dt = SnapshotPathProvider(
            service_config
        ).latest_snapshot_dt(
            repr(info_path),
            force_fs=service_config.filesystem.upper()
        )
        info_snapshot_path = SchemaTypedSnapshotFeaturePath(
            schema_path=info_path,
            snapshot_dt=info_latest_snapshot_dt
        )
        info_filepath = f"{repr(info_snapshot_path)}/data.json"
        feedback_ratio_info_dict: dict = orjson.loads(
            file_service.load(path=info_filepath).decode('utf-8')
        )

        return feedback_ratio_info_dict

    @time_it(LOGGER)
    def serve(self, entities: List[ItemSearchBasedFeatureEntity]) -> List[ItemFeedbackYnRatioEntity]:
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

        feature_entities: List[ItemFeedbackYnRatioEntity] = []
        search_ids: List[str] = []
        for i in range(len(search_result)):
            source = search_result[i]["_source"]
            positive_ratio = self.feedback_ratio_info["mean"]["bipolar"]
            try:
                document = SearchDocument.model_validate(source)
                positive_ratio = document.get_positive_ratio(self.feedback_ratio_info["mean"]["bipolar"])
            except ValidationError as ve:
                LOGGER.error(f"{__class__.__name__} {source} {ve}")
            # document = SearchDocument.model_validate(SearchDocument.dummy_obj())

            feature_entity: ItemFeedbackYnRatioEntity = ItemFeedbackYnRatioEntity(
                item_sid=document.item_sid,
                user_account_sid=user_account_sid,
                recommendation_sid=recommendation_sid,
                positive_ratio=positive_ratio,
            )
            feature_entities.append(feature_entity)
            search_ids.append(document.item_sid)

        sort_entities = []
        for tid in item_sids:
            if tid in search_ids:
                entity = feature_entities[search_ids.index(tid)] 
            else:
                entity = ItemFeedbackYnRatioEntity(
                    item_sid=tid,
                    user_account_sid=user_account_sid,
                    recommendation_sid=recommendation_sid,
                    positive_ratio=self.feedback_ratio_info["mean"]["bipolar"],
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
        
