from typing import Optional

from tunip.file_utils import services as file_services
from tunip.path.mart.factory import (
    VectorsItem2VectorPathFactory,
    VectorsVector2ItemPathFactory
)


class VectorIdMapper:
    def __init__(self, service_config, task_name, source_type, index_type, snapshot):
        self.service_config = service_config

        self.task_name = task_name
        self.source_type = source_type
        self.index_type = index_type
        self.snapshot = snapshot

        self.file_service = file_services.get(
            self.service_config.filesystem.upper(), config=self.service_config.config
        )

        i2v_path = VectorsItem2VectorPathFactory.create(
            task_name=self.task_name,
            user_name=self.service_config.username,
            source_type=self.source_type,
            index_type=self.index_type,
            snapshot_dt=self.snapshot
        )
        i2v_filepath = f"{i2v_path}/item2vec_id.pkl"

        v2i_path = VectorsVector2ItemPathFactory.create(
            task_name=task_name,
            user_name=self.service_config.username,
            source_type=self.source_type,
            index_type=self.index_type,
            snapshot_dt=self.snapshot
        )
        v2i_filepath = f"{v2i_path}/vec2item_id.pkl"

        self.item2vec_dict = self.file_service.loads_pickle(i2v_filepath)
        self.vec2item_dict = self.file_service.loads_pickle(v2i_filepath)

    def get_item_id(self, vec_id) -> Optional[str]:
        item_id = None
        try:
            item_id = self.vec2item_dict[vec_id]
        except KeyError:
            item_id = None
        finally:
            return item_id

    def get_vec_id(self, item_id) -> int:
        vec_id = -1
        try:
            vec_id = self.item2vec_dict[item_id]
        except KeyError:
            vec_id = -1
        finally:
            return vec_id


# from tunip.service_config import get_service_config
# service_config = get_service_config()
# print(service_config.config.dict)

# # task_name='document'
# # source_type='wiki'
# # snapshot='20211210_123718_461073'

# task_name='entity'
# source_type='wiki.small'
# snapshot='20220218_152242_772498'

# id_mapper = VectorIdMapper(service_config, task_name, source_type, snapshot)

# item_id = id_mapper.get_item_id(10)
# print(item_id)
