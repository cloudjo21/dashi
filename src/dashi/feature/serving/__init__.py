from pydantic import BaseModel
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from tunip.service_config import get_service_config


class ItemFeatureEntity(BaseModel):
    item_sid: str
 

class RecommendationFeatureEntity(ItemFeatureEntity):
    user_account_sid: str
    recommendation_sid: str


class NoUserException(Exception):
    pass
class InvalidUserAccountSidException(Exception):
    pass

class NoItemException(Exception):
    pass
class InvalidItemAccountSidException(Exception):
    pass


class ItemFeatureServable:
    pass

class SearchRequestable:
    pass

class HttpSearchRequestable(SearchRequestable):
    pass

class NonSearchRequestable(SearchRequestable):
    pass


async def build_searcher(session, searcher, entities):
    return await searcher.search(session, entities)


service_config = get_service_config()

elastic_host = service_config.elastic_host
headers = {'Content-Type': 'application/json; charset=utf-8'}
SESSION_TIMEOUT = 5

num_retries = 3
backoff_factor = 0.5
status_forcelist = [500, 502, 504]
retries = Retry(
    total=num_retries,
    read=num_retries,
    backoff_factor=backoff_factor,
    status_forcelist=status_forcelist
)
adapter = HTTPAdapter(max_retries=retries, pool_connections=4, pool_maxsize=40)

request_session = Session()
request_session.mount(elastic_host, adapter)

