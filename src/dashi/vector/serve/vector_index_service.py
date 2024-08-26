try:
    import faiss
except:
    pass

import numpy as np

from abc import abstractmethod
from typing import Dict, List, Optional


from tunip.env import NAUTS_LOCAL_ROOT
from tunip.es_utils import (
    init_elastic_client,
    search_knn_query,
    search_query_ids,
)
from tunip.file_utils import HttpBasedWebHdfsFileHandler
from tunip.path.mart.factory import VectorIndexPathFactory
from tunip.path_utils import services as path_services
from tunip.service_config import ServiceLevelConfig

from dashi import LOGGER
from dashi.vector import (
    DomainInfo,
    SearchIndexInfo,
    TaskInfo,
    VectorMetricType,
    VectorIndexRequest,
    VectorIndexResponse,
    VectorIndexResult,
    VectorIndexByItemIdsRequest,
    VectorIndexByItemIdsResponse
)
from dashi.vector.serve.vector_id_mapper import VectorIdMapper


class NotImplementedSearchByVectorIdsException(Exception):
    pass


class VectorIndex:
    pass

class ArrowVectorIndex:
    def __init__(self, index_path, nprobe=1):
        self.index_path = f"{index_path}/vector.index"

        self.index = faiss.read_index(self.index_path)
        self.index.nprobe = nprobe
    
    def search(self, q_vector, k=10):
        res = self.index.search(q_vector, k)
        return VectorIndexResult(res[0], res[1])

    def search_by_ids(self, vids) -> Optional[np.ndarray]:
        vectors = None
        try:
            vectors = self.index.reconstruct_batch(vids)
        except RuntimeError as re:
            LOGGER.warning(f"{vids} are requested to Arrow Vector Index but some vids are not.")
        finally:
            return vectors


class SearchEngineVectorIndex:
    def __init__(self, service_config: ServiceLevelConfig):
        self.search_client = init_elastic_client(service_config)


class VectorIndexFactory:
    @classmethod
    def create(cls, index_type: str):
        if index_type == "SEARCH_ENGINE":
            # SearchEngineVectorIndex()
            pass
        elif index_type == "ARROW":
            # ArrowVectorIndex()
            pass
        else:
            pass


class VectorIndexService:
    def __init__(self, service_config: ServiceLevelConfig, search_info: SearchIndexInfo):
        self.service_config = service_config
        self.search_info = search_info

    @abstractmethod
    def search(self, q_vector, k=10) -> VectorIndexResponse:
        pass

    @abstractmethod
    def search_by_item_ids(self, item_ids) -> (Optional[np.ndarray], List[int]):
        pass

    # def get_results(self, item_ids):
    #     search_results = search_query_ids(
    #         self.req_session,
    #         host=self.search_info.origin.split(":")[0],
    #         port=self.search_info.origin.split(":")[1],
    #         index=self.search_info.index,
    #         ids=item_ids
    #     )
    #     # print(search_results)
    #     id2index = dict(map(lambda p: (p[1]['_id'], p[0]), enumerate(search_results['hits']['hits'])))
    #     results = []
    #     for _id in item_ids:
    #         result = search_results['hits']['hits'][id2index[str(_id)]]
    #         results.append(", ".join([result["_source"][field] for field in self.search_info.search_fields]))
    #     return results


class ArrowVectorIndexService(VectorIndexService):

    def __init__(
            self,
            service_config: ServiceLevelConfig,
            domain_name: str,
            vid2iid_map: VectorIdMapper,
            index_path: str,
            search_info: SearchIndexInfo,
            metric_type: VectorMetricType,
            nprobe: int=1
    ):
        super(ArrowVectorIndexService, self).__init__(service_config, search_info)

        self.index = ArrowVectorIndex(index_path, nprobe)  # TODO use VectorIndexFactory
        self.domain_name = domain_name
        self.vid2iid_map = vid2iid_map
        self.metric_type = metric_type

    def search(self, request: VectorIndexRequest) -> VectorIndexResponse:
        # TODO params like SearchEngineVectorIndexService
        # TODO and get_results default in this method
        # TODO proc by vector_metric_type
        if self.metric_type == VectorMetricType.COSINE_SIM:
            faiss.normalize_L2(request.q_vector)

        index_response = self.index.search(request.q_vector, request.top_k or self.search_info.top_k)

        LOGGER.info(f"index_response: {index_response}")

        item_ids = [
            list(filter(lambda iid: iid is not None, [self.vid2iid_map.get_item_id(vid) for vid in vids])) for vids in index_response.nn_ids
        ]
        return VectorIndexResponse(index_response, item_ids, status_code=200)

    def search_by_item_ids(self, item_ids) -> (Optional[np.ndarray], List[int]):
        vids = [self.vid2iid_map.get_vec_id(item_id) for item_id in item_ids]
        not_found_item_indexes = [ivf[0] for ivf in (filter(lambda iv: iv[1] < 0, enumerate(vids)))]
        vector_ids = list(filter(lambda vid: vid > -1, vids))
        if len(not_found_item_indexes) > 0:
            LOGGER.warning(f"iids={item_ids}, vids={vector_ids}, not_found_index={not_found_item_indexes}")
        return self.index.search_by_ids(vids=vector_ids), not_found_item_indexes

    
class SearchEngineVectorIndexService(VectorIndexService):
    def __init__(self, service_config: ServiceLevelConfig, search_info: SearchIndexInfo, metric_type: str):
        super(SearchEngineVectorIndexService, self).__init__(service_config, search_info)

        self.index = SearchEngineVectorIndex(service_config)  # TODO use VectorIndexFactory
        self.metric_type = metric_type
        self.search_client = init_elastic_client(service_config)
        self.searcheable = self.search_client.ping()

    def _get_postings(self, search_postings, row, target_fields):
        for field in target_fields:
            search_postings[field].append(row["_source"][field]) 
        return search_postings

    def _get_items(self, search_results, row, target_fields):
        result_dict = dict([(field, row["_source"][field]) for field in target_fields])
        search_results.append(result_dict)
        return search_results

    def _get_result_fn(self, search_result_type: str):
        if search_result_type == "POSTING":
            return self._get_postings
        else:
            return self._get_items

    def _get_default_result(self, search_result_type: str, target_fields: list):
        if search_result_type == "POSTING":
            return dict([(s, []) for s in target_fields])
        else:
            return []


    def search(self, request: VectorIndexRequest) -> VectorIndexResponse:
        assert request.search_result_type is not None
        if self.searcheable is False:
            return VectorIndexResponse(
                item_ids=[],
                status_code=503,
                status_message=f"CONNECTION ERROR TO {self.service_config.elastic_host}"
            )

        result = search_knn_query(
            es=self.search_client,
            index_name=self.search_info.index,
            query_field_name=self.search_info.query_field_name,
            query_vector=request.q_vector,
            source_fields=self.search_info.search_fields,
            top_k=request.top_k or self.search_info.top_k,
            num_candidates=request.num_candidates or self.search_info.num_candidates
        )
        rows = result["hits"]["hits"]

        target_fields = request.source_fields or self.search_info.search_fields

        scores = []
        ids = []

        # TODO refactoring VectorIndexResponseBuilder for each search_result_type
        search_results = self._get_default_result(request.search_result_type, target_fields)
        result_fn = self._get_result_fn(request.search_result_type)
        for row in rows:
            scores.append(row["_score"])
            ids.append(row["_source"][self.search_info.id_field])
            search_results = result_fn(search_results, row, target_fields)
            
        if request.search_result_type == "POSTING":
            search_results["score"] = scores
            response = VectorIndexResponse(
                item_ids=ids,
                search_postings=search_results
            )
        else:
            response = VectorIndexResponse(
                item_ids=ids,
                search_items=search_results
            )

        return response

    def search_by_item_ids(self, item_ids) -> (Optional[np.ndarray], List[int]):
        raise NotImplementedSearchByVectorIdsException()


class VectorIndexServiceFactory:
    @classmethod
    def create(cls, service_config: ServiceLevelConfig, domain_info: DomainInfo, task_info: TaskInfo) -> VectorIndexService:

        if task_info.index_type == "SEARCH_ENGINE":
            return SearchEngineVectorIndexService(service_config, domain_info.search_info, domain_info.metric_type)
        else:
            vector_index_nauts_path = VectorIndexPathFactory.create(
                task_name=task_info.name,
                user_name=service_config.username,
                source_type=task_info.source_type,
                index_type=task_info.index_type,
                snapshot_dt=domain_info.snapshot
            )
            vector_index_nauts_filepath = f"{vector_index_nauts_path}/vector.index"
            # download index
            if service_config.has_hdfs_fs:
                webhdfs = HttpBasedWebHdfsFileHandler(service_config)
                webhdfs.download(
                    hdfs_path=str(vector_index_nauts_filepath),
                    overwrite=True,
                    read_mode='rb',
                    write_mode='wb'
                )

            local_path_service = path_services.get("LOCAL", config=service_config.config)
            vector_index_service_path = local_path_service.build(str(vector_index_nauts_path))
            id_mapper = VectorIdMapper(
                service_config,
                task_info.name,
                task_info.source_type,
                task_info.index_type,
                domain_info.snapshot
            )
            index_service = ArrowVectorIndexService(
                service_config=service_config,
                domain_name=domain_info.domain,
                vid2iid_map=id_mapper,
                index_path=vector_index_service_path,
                search_info=domain_info.search_info,
                metric_type=domain_info.metric_type
            )
            return index_service



class VectorIndexCollectionService:

    def __init__(self, service_config, domain_coll_info):
        # TODO fix get_service_repo_dir
        self.service_path = NAUTS_LOCAL_ROOT

        self.domain_coll_info = domain_coll_info
        self.domain2index: Dict[int, VectorIndexService] = dict()
        self.task2id = dict() # dict[str, int]

        for domain_info in domain_coll_info.service_tasks:
        # for domain_name, domain_info in domain_coll_info.domain2info.items():
            task_info = domain_info.task_info
            
            if domain_info.id not in self.domain2index:

                LOGGER.info(f"Vector Index Service Loaded - DOMAIN: {domain_info}")

                self.domain2index[domain_info.id] = VectorIndexServiceFactory.create(
                    service_config=service_config,
                    domain_info=domain_info,
                    task_info=task_info
                )

                self.task2id[f"{domain_info.domain}+{domain_info.task_info.name}"] = domain_info.id
    

    def search(self, request: VectorIndexRequest) -> VectorIndexResponse:
        domain = request.domain
        task = request.task

        task_key = f"{domain}+{task}"
        service_id = self.task2id.get(task_key)
        if service_id is None:
            LOGGER.warning(f"NO SERVICE FOR service_id: {service_id}, service_task_name: {domain}+{task}, q_vector")
            return [], f'NO_SERVICE_FOR_{domain}+{task}'
        LOGGER.info(f'{request.domain}, {request.task}, {request.search_result_type}, {request.top_k}, {request.source_fields}')

        index_service = self.domain2index[self.task2id[task_key]]
        index_response: VectorIndexResponse = index_service.search(request)
        return index_response


    def search_by_item_ids(self, request: VectorIndexByItemIdsRequest) -> VectorIndexByItemIdsResponse:
        domain = request.domain
        task = request.task

        task_key = f"{domain}+{task}"
        service_id = self.task2id.get(task_key)
        if service_id is None:
            LOGGER.warning(f"NO SERVICE FOR service_id: {service_id}, service_task_name: {domain}+{task}, q_vector")
            return VectorIndexByItemIdsResponse(None, None)
        # LOGGER.info(f'{request.domain}, {request.task}, {request.item_ids}')

        index_service: VectorIndexService = self.domain2index[self.task2id[task_key]]
        result_tuple: (Optional[np.ndarray], List[int]) = index_service.search_by_item_ids(request.item_ids)
        return VectorIndexByItemIdsResponse(nn_vectors=result_tuple[0], not_found_indexes=result_tuple[1])
