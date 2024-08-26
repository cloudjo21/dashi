import json

from tunip import file_utils
from tunip.env import JSON_GZ_SUFFIX, JSON_SUFFIX
from tunip.path_utils import has_suffix_among

from tunip.path.lake.serp import (
    LakeSerpContentsDetailsDomainSnapshotPath,
    LakeSerpContentsFormatDomainSnapshotPath,
)

from dashi.utils.deploys import MultiTaskServiceDeploy


class ContentsService:
    def __init__(self, stat_type, content_dict):
        self.stat_type = stat_type
        self.content_dict = content_dict

    def search(self, texts):
        try:
            return self.content_dict[texts]
        except KeyError:
            return []


class ContentsCollectionService:
    def __init__(self, service_config, contents_coll_info: MultiTaskServiceDeploy):
        self.contents2service = dict()
        self.task2id = dict()  # dict[str, int]
        for service_id, contents_info in enumerate(contents_coll_info.service_tasks):
            task_info = contents_info.task_info
            if contents_info.stat_type == "count":
                contents_nauts_path = LakeSerpContentsFormatDomainSnapshotPath(
                    user_name=service_config.username,
                    entity_type=task_info.entity_type,
                    domain_name=task_info.domain_name,
                    snapshot_dt=contents_info.snapshot
                )
                contents_type = 'contents_format'
            elif contents_info.stat_type == "length":
                contents_nauts_path = LakeSerpContentsDetailsDomainSnapshotPath(
                    user_name=service_config.username,
                    entity_type=task_info.entity_type,
                    domain_name=task_info.domain_name,
                    snapshot_dt=contents_info.snapshot,
                )
                contents_type = "contents_details"

            file_service = file_utils.services.get("HDFS", config=service_config.config)
            files = file_service.list_dir(str(contents_nauts_path))
            files = list(
                filter(
                    lambda p: has_suffix_among(p, [JSON_SUFFIX, JSON_GZ_SUFFIX]), files
                )
            )

            keyword2value_stat = dict()
            for f in files:
                f = file_service.open(f)
                lines = f.readlines()
                objs = filter(
                    lambda o: o["result"] != "{}", [json.loads(j) for j in lines]
                )

                for o in objs:
                    keyword2value_stat[o["keyword"]] = []
                    result_o = json.loads(o["result"])
                    for feat in result_o[contents_type]:
                        if feat["value_type"] == contents_info.stat_type:
                            keyword2value_stat[o["keyword"]].append(
                                {
                                    "feature_type": feat["feature_type"],
                                    "value": feat["value"],
                                }
                            )

                            # TODO push samples to message queue
                            # import random
                            # n = random.random()
                            # if n < 0.01:
                            #     print(f"{feat['value_type']}, {o['keyword']}, {feat['feature_type'], feat['value']}")

            contents_service = ContentsService(
                contents_info.stat_type, keyword2value_stat
            )
            self.contents2service[service_id] = contents_service
            self.task2id[
                f"{contents_info.domain}+{contents_info.stat_type}"
            ] = service_id

    def search(self, domain, stat_type, texts):
        service_id = self.task2id.get(f"{domain}+{stat_type}")
        print(
            f"service_id: {service_id}, service_task_name: {domain}+{stat_type}, texts: {texts}"
        )
        if service_id is None:
            return [], f"NO_SERVICE_FOR_{domain}+{stat_type}"

        domain_service = self.contents2service[service_id]

        return domain_service.search(texts), "OK"
