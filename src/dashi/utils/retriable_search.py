from abc import ABC

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class RetriableSearchService(ABC):
    def __init__(self, service_config):
        self.service_config = service_config

        self.elastic_host = self.service_config.elastic_host
        self.headers = {'Content-Type': 'application/json; charset=utf-8'}
        self.timeout = 3

        num_retries = 3
        backoff_factor = 0.5
        status_forcelist = [500, 502, 504]
        retries = Retry(
            total=num_retries,
            read=num_retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist
        )
        adapter = HTTPAdapter(max_retries=retries)
        
        self.request_session = Session()
        self.request_session.mount(self.elastic_host, adapter)
