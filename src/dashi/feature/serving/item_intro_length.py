import orjson

from typing import Dict, List, Optional
from pydantic import BaseModel, ValidationError

from tunip.time_it import time_it

from dashi import LOGGER
from dashi.feature.serving import SESSION_TIMEOUT
from dashi.feature.serving.messages import ItemSearchBasedFeatureEntity


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
                        "item_introduction"
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

    item_introduction: Optional[str] = None

    def get_intro_len(self):
        if self.item_introduction:
            return len(self.item_introduction)
        else:
            return 0

    @staticmethod
    def dummy_obj():
        return SearchDocument(
            item_sid="2159758c-41a8-44d0-a039-70c109d1b4cb",
            item_introduction=''
        ).dict()


class ItemIntroLengthEntity(BaseModel):
    user_account_sid: str

    item_sid: str
    recommendation_sid: str

    intro_len: int = 0


class ItemIntroLength:

    def __init__(self, service_config, request_session):
        self.index_name = "item_info"

        self.service_config = service_config
        self.request_session = request_session

    @time_it(LOGGER)
    def serve(self, entities: List[ItemSearchBasedFeatureEntity]) -> List[ItemIntroLengthEntity]:
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

        feature_entities: List[ItemIntroLengthEntity] = []
        search_ids: List[str] = []
        for i in range(len(search_result)):
            source = search_result[i]["_source"]
            intro_len = 0
            try:
                document = SearchDocument.model_validate(source)
                intro_len=document.get_intro_len()
            except ValidationError as ve:
                LOGGER.error(f"{__class__.__name__} {source} {ve}")
            # document = SearchDocument.model_validate(SearchDocument.dummy_obj())

            entity: ItemIntroLengthEntity = ItemIntroLengthEntity(
                item_sid=document.item_sid,
                user_account_sid=user_account_sid,
                recommendation_sid=recommendation_sid,
                intro_len=intro_len,
            )
            feature_entities.append(entity)
            search_ids.append(document.item_sid)

        sort_entities = []
        for tid in item_sids:
            if tid in search_ids:
                entity = feature_entities[search_ids.index(tid)] 
            else:
                entity = ItemIntroLengthEntity(
                    item_sid=tid,
                    user_account_sid=user_account_sid,
                    recommendation_sid=recommendation_sid,
                    intro_len=0,
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
        
