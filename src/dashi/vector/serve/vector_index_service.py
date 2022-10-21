import faiss
import numpy as np
import requests

from dataclasses import dataclass
from typing import Dict, List


from tunip.env import NAUTS_LOCAL_ROOT
from tunip.es_utils import search_query_ids
from tunip.file_utils import HttpBasedWebHdfsFileHandler
from tunip.path_utils import services as path_services
from tunip.path.mart.factory import VectorIndexPathFactory
from tunip.path_utils import get_service_repo_dir
from tunip.service_config import ServiceLevelConfig, get_service_config

from dashi import LOGGER
from dashi.vector import (
    DomainCollectionInfo,
    VectorMetricType,
    VectorIndexResponse,
    VectorIndexResult
)
from dashi.vector.serve.vector_id_mapper import VectorIdMapper


class VectorIndex:
    def __init__(self, index_path, nprobe=1):
        self.index_path = f"{index_path}/vector.index"

        self.index = faiss.read_index(self.index_path)
        self.index.nprobe = nprobe
    
    def search(self, q_vector, k=10):
        res = self.index.search(q_vector, k)
        return VectorIndexResult(res[0], res[1])


@dataclass
class VectorIndexResponse(VectorIndexResponse):
    vector_index_res: VectorIndexResult
    item_ids: List[int]


class VectorIndexService:

    def __init__(self, domain_name, vid2iid_map, index_path, search_info, metric_type, nprobe=1):
        self.domain_name = domain_name
        self.vid2iid_map = vid2iid_map
        self.index = VectorIndex(index_path, nprobe)
        self.req_session = requests.Session()
        self.search_info = search_info
        self.metric_type = metric_type

    def search(self, q_vector, k=10) -> VectorIndexResponse:
        # TODO proc by vector_metric_type
        if self.metric_type == VectorMetricType.COSINE_SIM:
            faiss.normalize_L2(q_vector)

        index_response = self.index.search(q_vector, k)

        LOGGER.info(f"index_response: {index_response}")

        item_ids = [
            list(filter(lambda iid: iid > -1, [self.vid2iid_map.get_item_id(vid) for vid in vids])) for vids in index_response.nn_ids
        ]
        return VectorIndexResponse(index_response, item_ids)

    def get_results(self, item_ids):
        search_results = search_query_ids(
            self.req_session,
            host=self.search_info.origin.split(":")[0],
            port=self.search_info.origin.split(":")[1],
            index=self.search_info.index,
            ids=item_ids
        )
        # print(search_results)
        id2index = dict(map(lambda p: (p[1]['_id'], p[0]), enumerate(search_results['hits']['hits'])))
        results = []
        for _id in item_ids:
            result = search_results['hits']['hits'][id2index[str(_id)]]
            results.append(", ".join([result["_source"][field] for field in self.search_info.search_fields]))
        return results
        # return [", ".join([source_res["_source"][field] for field in self.search_info.search_fields]) for source_res in search_results['hits']['hits']]


class VectorIndexCollectionService:

    def __init__(self, service_config, domain_coll_info):
        # TODO fix get_service_repo_dir
        self.service_path = NAUTS_LOCAL_ROOT

        self.domain_coll_info = domain_coll_info
        self.domain2index: Dict[int, VectorIndexService] = dict()
        self.task2id = dict() # dict[str, int]

        if service_config.has_hdfs_fs:
            webhdfs = HttpBasedWebHdfsFileHandler(service_config)
        local_path_service = path_services.get("LOCAL", config=service_config.config)
        
        for domain_info in domain_coll_info.service_tasks:
        # for domain_name, domain_info in domain_coll_info.domain2info.items():
            task_info = domain_info.task_info
            search_info = domain_info.search_info
            metric_type = domain_info.metric_type
            
            vector_index_nauts_path = VectorIndexPathFactory.create(
                task_name=task_info.name,
                user_name=service_config.username,
                source_type=task_info.source_type,
                index_type=task_info.index_type,
                snapshot_dt=domain_info.snapshot
            )
            vector_index_nauts_filepath = f"{vector_index_nauts_path}/vector.index"

            if domain_info.id not in self.domain2index:

                # download index
                if service_config.has_hdfs_fs:
                    webhdfs.download(
                        hdfs_path=str(vector_index_nauts_filepath),
                        overwrite=True,
                        read_mode='rb',
                        write_mode='wb'
                    )
                vector_index_service_path = local_path_service.build(str(vector_index_nauts_path))

                id_mapper = VectorIdMapper(
                    service_config,
                    task_info.name,
                    task_info.source_type,
                    task_info.index_type,
                    domain_info.snapshot
                )
                self.domain2index[domain_info.id] = VectorIndexService(
                    domain_name=domain_info.domain,
                    vid2iid_map=id_mapper,
                    index_path=vector_index_service_path,
                    search_info=search_info,
                    metric_type=metric_type
                )
                self.task2id[f"{domain_info.domain}+{domain_info.task_info.name}"] = domain_info.id
    

    def search(self, domain, task, q_vector) -> VectorIndexResponse:
        service_id = self.task2id.get(f"{domain}+{task}")
        print(f"service_id: {service_id}, service_task_name: {domain}+{task}, q_vector")
        if service_id is None:
            return [], f'NO_SERVICE_FOR_{domain}+{task}'

        index_service = self.domain2index[service_id]
        response = index_service.search(q_vector, k=10)

        search_results = []
        for item_ids in response.item_ids:
            results = index_service.get_results(item_ids)
            search_results.append(results)
        response.search_results = search_results

        return response
