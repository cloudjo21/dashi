from typing import Optional

from tunip import LOGGER
from tunip.es_utils import (
    init_elastic_client,
    search_query,
    search_filter_many_values
)
from tunip.service_config import ServiceLevelConfig


class ItemSearchService:
    def __init__(self, service_config: ServiceLevelConfig, search_index_name: str):
        self.search_client = init_elastic_client(service_config)
        self.search_index_name = search_index_name

    def search_items(self, query_field_name: str, values: list, source_fields: list) -> Optional[iter]:
        try:
            rows = search_filter_many_values(
                self.search_client,
                self.search_index_name,
                query_field_name,
                values,
                source_fields
            )
        except:
            rows = None
        finally:
            if rows:
                return iter(rows)
            else:
                return rows

    def search_query(self, query: dict, source_fields: list, size: int) -> Optional[iter]:
        try:
            rows = search_query(
                es=self.search_client, index_name=self.search_index_name, query=query, source_fields=source_fields, strict_fields=False, size=size
            )
        except Exception as e:
            rows = None
            LOGGER.error(str(e))
        finally:
            if rows:
                return iter(rows)
            else:
                return rows
