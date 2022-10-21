from pathlib import Path

from tunip import path_utils
from tunip.path_utils import (
    EvalCorpusDomainPath,
    EvalCorpusConditionalPath,
    get_latest_path_for_prefix
)
from tunip.env import NAUTS_LOCAL_ROOT
from tunip.service_config import get_service_config
from shellington.data.eval_item_loader_factory import EvalItemLoaderFactory

from dashi.utils.deploys import MultiEvalServiceDeploy

config = get_service_config()
path_provider = path_utils.services.get("LOCAL", config=config.config)  


class DomainEvalService:
    def __init__(self, service_id, domain_name, task_name, evaluator_config):
        self.service_id = service_id
        self.domain_name = domain_name
        self.task_name = task_name
        self.task_type = evaluator_config.get("task_type")
        self.eval_corpus_cond_path = self._get_result_path(evaluator_config)
        self.item_loader = EvalItemLoaderFactory.create(self.task_type)

    def search(self, eval_item, label):
        
        file_name = self.item_loader.load(eval_item, label, self.eval_corpus_cond_path)
        file_path = path_provider.build(f"{str(self.eval_corpus_cond_path)}/{file_name}")
        
        return file_path
        
    def _get_result_path(self, evaluator_config):
        
        snapshot_dt = evaluator_config.get("snapshot_dt")
        target_corpus_dt = evaluator_config.get("target_corpus_dt")
        
        eval_corpus_domain_path = EvalCorpusDomainPath(
            user_name=config.username,
            domain_name=self.domain_name,
            snapshot_dt=snapshot_dt,
        )

        checkpoint = Path(get_latest_path_for_prefix(
            f"{NAUTS_LOCAL_ROOT}{eval_corpus_domain_path}/model", "checkpoint-")).name
        
        condition_name = "except_undefined_labels"

        eval_corpus_cond_path = EvalCorpusConditionalPath(
            user_name=config.username,
            domain_name=self.domain_name,
            snapshot_dt=evaluator_config.get("snapshot_dt"),
            checkpoint=checkpoint,
            task_name=self.task_name,
            condition_name=condition_name,
            target_corpus_dt=target_corpus_dt,
        )
        return eval_corpus_cond_path
    
    
class CollectionEvalService:
    def __init__(self, eval_service_deploy: MultiEvalServiceDeploy):
        print(f"INIT DEPLOY:\n{eval_service_deploy}")
        self.domain2service = dict() # dict[int, DomainEvalService]
        self.task2id = dict() # dict[str, int]
        for service_id, service_task in enumerate(eval_service_deploy.service_tasks):
            domain_service = DomainEvalService(
                service_id,
                service_task.domain,
                service_task.task_name,
                service_task.evaluator_config
            )
            self.domain2service[service_id] = domain_service
            self.task2id[f"{service_task.domain}+{service_task.task_name}"] = service_id

        print(self.task2id)
        
    def search(self, domain, task, eval_item, label):
        service_id = self.task2id.get(f"{domain}+{task}")
        print(f"service_id: {service_id}, service_task_name: {domain}+{task}, eval_item: {eval_item}")
        if service_id is None:
            return [], f'NO_SERVICE_FOR_{domain}+{task}'

        domain_service = self.domain2service[service_id]
        return domain_service.search(eval_item, label)
