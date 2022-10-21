from tweak.predict.predictors import PredictorFactory

from dashi.utils.deploys import MultiPretrainingTaskServiceDeploy


class PreTrainedModelService:
    def __init__(self, service_id, model_name, predictor_config):
        self.service_id = service_id
        self.model_name = model_name
        self.predictor = PredictorFactory.create(predictor_config)
    
    def search(self, texts):
        return self.predictor.predict(texts)


class PreTrainedModelCollectionService:

    def __init__(self, model_service_deploy: MultiPretrainingTaskServiceDeploy):

        self.model2service = dict()
        self.task2id = dict()
        for service_id, service_task in enumerate(model_service_deploy.service_tasks):
            model_service = PreTrainedModelService(
                service_id,
                service_task.model_name,
                service_task.predictor_config
            )
            self.model2service[service_id] = model_service
            self.task2id[f"{service_task.model_name}"] = service_id

        print(self.task2id)

    def search(self, model_name, texts):
        service_id = self.task2id.get(model_name)
        print(f"service_id: {service_id}, service_task_name: {model_name}, texts: {' | '.join(texts)}")
        if service_id is None:
            return [], f'NO_SERVICE_FOR_{model_name}'

        model_service = self.model2service[service_id]
        return model_service.search(texts), 'OK'
