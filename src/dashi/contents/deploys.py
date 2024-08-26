from typing import List, Union
from pydantic import BaseModel

from dashi.contents import ContentsTaskInfo
from dashi.utils.deploys import (
    MultiTaskServiceDeploy,
    MultiPretrainingTaskServiceDeploy,
    MultiVectorSetTaskServiceDeploy,
    ServiceDeploy,
    TaskServiceDeploy,
)


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
