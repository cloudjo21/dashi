from pydantic import BaseModel
from typing import Dict

from tunip.service_config import ServiceLevelConfig
from tweak.predict.predictors import PredictorFactory

from dashi.utils.deploys import MultiTaskServiceDeploy


class DomainModelService:
    def __init__(self, service_id, domain_name, predictor_config):
        self.service_id = service_id
        self.domain_name = domain_name
        self.predictor = PredictorFactory.create(predictor_config)

    def search(self, texts):
        # return pred_results: list
        return self.predictor.predict(texts)


class CollectionModelService:
    def __init__(self, model_service_deploy: MultiTaskServiceDeploy):
        print(f"INIT DEPLOY:\n{model_service_deploy}")
        self.domain2service = dict() # dict[int, DomainModelService]
        self.task2id = dict() # dict[str, int]
        for service_id, service_task in enumerate(model_service_deploy.service_tasks):
            domain_service = DomainModelService(
                service_id,
                service_task.domain,
                service_task.predictor_config
            )
            self.domain2service[service_id] = domain_service
            self.task2id[f"{service_task.domain}+{service_task.task_name}"] = service_id

        print(self.task2id)


    def search(self, domain, task, texts):
        service_id = self.task2id.get(f"{domain}+{task}")
        print(f"service_id: {service_id}, service_task_name: {domain}+{task}, texts: {' | '.join(texts)}")
        if service_id is None:
            return [], f'NO_SERVICE_FOR_{domain}+{task}'

        domain_service = self.domain2service[service_id]
        return domain_service.search(texts), 'OK'
