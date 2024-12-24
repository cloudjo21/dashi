from abc import ABC
from enum import Enum
from pydantic import BaseModel, validator
from typing import List, Optional

from tweak.predict.predictor import PredictorConfig

from dashi.vector import SearchIndexInfo, TaskInfo, VectorMetricType


class ServiceDeploy(ABC):
    pass


class TaskServiceDeploy(ServiceDeploy):
    pass


class NncServiceDeploy(BaseModel, ServiceDeploy):
    model_name: str
    es_search_result_size: int
    distance_threshold: float


class SinglePretrainingTaskServiceDeploy(BaseModel, ServiceDeploy):
    model_name: str
    predictor_config: PredictorConfig

class MultiPretrainingTaskServiceDeploy(BaseModel, ServiceDeploy):
    service_tasks: List[SinglePretrainingTaskServiceDeploy]
    service_type: str = 'PRETRAINED_MODEL'


class SingleTaskServiceDeploy(BaseModel, TaskServiceDeploy):
    domain: str
    task_name: str
    predictor_config: PredictorConfig

    @property
    def domain_name(self):
        return self.domain

    @property
    def task_names(self):
        return self.task_name


class MultiTaskServiceDeploy(BaseModel, ServiceDeploy):
    service_tasks: List[SingleTaskServiceDeploy]
    service_type: str = 'MODEL'

    @property
    def domain_name(self):
        return self.service_tasks[0].domain
    
    @property
    def task_names(self):
        return [deploy.task_name for deploy in self.service_tasks]

    def has_task_name(self, task_name):
        return task_name in [deploy.task_name for deploy in self.service_tasks]
    
    @property
    def task_mapping(self):
        return {self.domain_name: self.task_names}

    def index_of(self, domain_name: str, task_name: str):
        for i, service_task in enumerate(self.service_tasks):
            if service_task.domain_name == domain_name and service_task.task_name == task_name:
                return i
        return -1


class VectorSetType(Enum):
    DOCUMENT = 0
    ENTITY = 1

    def describe(self):
        return self.name, self.value


class SingleVectorSetTaskServiceDeploy(BaseModel, TaskServiceDeploy):
    id: int
    domain: str
    snapshot: str
    task_info: TaskInfo
    search_info: Optional[SearchIndexInfo] = None
    metric_type: Optional[VectorMetricType] = VectorMetricType.COSINE_SIM

    # vector_set_type: VectorSetType
    # dt_snapshot: str

    # @validator('vector_set_type')
    # def vector_set_type_to_enum(cls, _vector_set_type):
    #     return VectorSetType[_vector_set_type]


class MultiVectorSetTaskServiceDeploy(BaseModel, ServiceDeploy):
    service_tasks: List[SingleVectorSetTaskServiceDeploy]
    service_type: str = 'VECTOR'

    @property
    def task_mapping(self):
        return self.service_tasks

    def get_service_task(self, domain: str) -> Optional[TaskServiceDeploy]:
        tasks_deployed = list(filter(lambda s: s.domain == domain, self.service_tasks)) or None
        return tasks_deployed[0] if tasks_deployed else None
    
    def get_domain_names(self):
        return [service.domain for service in self.service_tasks]

class SingleEvalServiceDeploy(BaseModel, TaskServiceDeploy):
    domain: str
    task_name: str
    evaluator_config: dict

    @property
    def domain_name(self):
        return self.domain

    @property
    def task_names(self):
        return self.task_name

class MultiEvalServiceDeploy(BaseModel, ServiceDeploy):
    service_tasks: List[SingleEvalServiceDeploy]
    service_type: str = 'EVAL'

    @property
    def domain_name(self):
        return self.service_tasks[0].domain
    
    @property
    def task_names(self):
        return [deploy.task_name for deploy in self.service_tasks]

    def has_task_name(self, task_name):
        return task_name in [deploy.task_name for deploy in self.service_tasks]
    
    @property
    def task_mapping(self):
        return {self.domain_name: self.task_names}
