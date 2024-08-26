import numpy as np

from enum import Enum
from pydantic import BaseModel, validator
from typing import Dict, List, Optional

from dashi import DashiResponse


class VectorMetricType(Enum):
    COSINE_SIM = 0
    L2_DIST = 1


class TaskInfo(BaseModel):
    name: str
    source_type: str
    index_type: str


class DomainInfo(BaseModel):
    id: int
    domain: str
    snapshot: str
    task_info: Optional[TaskInfo] = None
    metric_type: Optional[VectorMetricType] = VectorMetricType.COSINE_SIM


class DomainCollectionInfo(BaseModel):
    domain2info: Dict[str, DomainInfo]


class SearchIndexInfo(BaseModel):
    index: str
    origin: str
    search_fields: List[str]
    top_k: int
    query_field_name: Optional[str]
    id_field: Optional[str]
    num_candidates: Optional[int]


class VectorIndexResult(BaseModel):
    nn_distances: np.ndarray
    nn_ids: np.ndarray

    @validator('nn_distances', pre=True)
    def parse_nn_distances(v):
      return np.array(v, dtype=float)

    @validator('nn_ids', pre=True)
    def parse_nn_ids(v):
      return np.array(v, dtype=int)

    class Config:
        arbitrary_types_allowed = True


# class VectorIndexByItemIdsResult(BaseModel):
#     nn_vectors: np.ndarray

#     class Config:
#         arbitrary_types_allowed = True


class VectorIndexRequest(BaseModel):
    domain: str
    task: str
    q_vector: List[float]
    search_result_type: Optional[str] = "POSTING"  # TODO let search_result_type enum
    top_k: Optional[int] = 20
    num_candidates: Optional[int] = 50
    source_fields: Optional[list]

class VectorIndexResponse(DashiResponse):
    item_ids: List[str]
    vector_index_res: Optional[VectorIndexResult]
    search_postings: Optional[dict]  # Dict[List[dict]]
    search_items: Optional[list]  # List[dict]

    class Config:
        arbitrary_types_allowed = True


class VectorIndexByItemIdsRequest(BaseModel):
    domain: str
    task: str
    q_vector: List[float]
    item_ids: List[str]

class VectorIndexByItemIdsResponse(BaseModel):
    nn_vectors: Optional[np.ndarray]
    not_found_indexes: Optional[List[int]]

    class Config:
        arbitrary_types_allowed = True

    # vector_index_res: Optional[VectorIndexByItemIdsResult]

    def has_valid_vectors(self):
        return (self.nn_vectors is not None) and self.nn_vectors.any()
