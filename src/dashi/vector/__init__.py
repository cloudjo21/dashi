import numpy as np

from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel
from typing import Dict, List, Optional


class TaskInfo(BaseModel):
    name: str
    source_type: str
    index_type: str


class DomainInfo(BaseModel):
    id: int
    domain: str
    snapshot: str
    task_info: Optional[TaskInfo] = None


class DomainCollectionInfo(BaseModel):
    domain2info: Dict[str, DomainInfo]


class SearchIndexInfo(BaseModel):
    index: str
    origin: str
    search_fields: List[str]


class VectorIndexRequest:
    pass


class VectorIndexResponse:
    pass


@dataclass
class VectorIndexResult:
    nn_distances: np.ndarray
    nn_ids: np.ndarray


class VectorMetricType(Enum):
    COSINE_SIM = 0
    L2_DIST = 1
