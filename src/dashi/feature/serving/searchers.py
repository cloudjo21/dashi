from dashi.feature.serving.messages import ItemSearchBasedFeatureEntity
from typing import List

from aiohttp import ClientSession, ClientResponse


class ItemSearcher:
    pass

class ItemMGetSearcher(ItemSearcher):
    def __init__(self, search_host, index_name, query_builder):
        self.search_host = search_host
        self.index_name = index_name
        self.query_builder = query_builder

    async def search(self, request_session: ClientSession, entities: List[ItemSearchBasedFeatureEntity]):
        item_sids = [e.item_sid for e in entities]
        query = self.query_builder.apply(item_sids)
        response = request_session.post(
            url=f"{self.search_host}/_mget",
            json=query,
            headers={'Content-Type': 'application/json; charset=utf-8'},
            # f"{self.service_config.elastic_host}/{self.index_name}/_search",
            # data=orjson.dumps(query).decode("utf-8"),
            # timeout=SESSION_TIMEOUT
        )
        query_result = await response.json()
        search_result = query_result["docs"]
        return search_result
