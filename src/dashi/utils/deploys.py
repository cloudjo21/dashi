from abc import ABC
from enum import Enum
from pydantic import BaseModel, validator
from typing import List, Optional, Union

from tunip.task.task_set import TaskSet, TaskType
from tunip.yaml_loader import YamlLoader

from tweak.predict.predictor import PredictorConfig

from dashi.vector import SearchIndexInfo, TaskInfo, VectorMetricType
from dashi.contents import ContentsTaskInfo


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


class VectorSetType(Enum):
    DOCUMENT = 0
    ENTITY = 1

    def describe(self):
        return self.name, value


class SingleVectorSetTaskServiceDeploy(BaseModel, TaskServiceDeploy):
    id: int
    domain: str
    snapshot: str
    task_info: TaskInfo
    search_info: Optional[SearchIndexInfo]
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


class SingleContentsTaskServiceDeploy(BaseModel, TaskServiceDeploy):
    domain: str
    stat_type: str
    snapshot: str
    task_info: ContentsTaskInfo


class MultiContentsTaskServiceDeploy(BaseModel, ServiceDeploy):
    service_tasks: List[SingleContentsTaskServiceDeploy]
    service_type: str = 'CONTENTS'

    @property
    def task_mapping(self):
        return self.service_tasks


class CompositeServiceDeploy(BaseModel, ServiceDeploy):
    service_root: List[Union[
        MultiTaskServiceDeploy,
        MultiPretrainingTaskServiceDeploy,
        MultiVectorSetTaskServiceDeploy,
        MultiContentsTaskServiceDeploy
    ]]


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
