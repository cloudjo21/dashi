import json
import unittest

from tunip import file_utils
from tunip.env import JSON_GZ_SUFFIX, JSON_SUFFIX
from tunip.service_config import get_service_config
from tunip.path_utils import has_suffix_among


class LoadContentsStatTest(unittest.TestCase):

    def setUp(self):

        service_config = get_service_config()
        self.file_service = file_utils.services.get("HDFS", config=service_config.config)

    def test_get_contents_format(self):

        stat_type = 'count'
        stat_path = '/user/nauts/lake/serp/query/stat/entity/cosmetic/20220316_130000_000000'

        files = self.file_service.list_dir(stat_path)
        files = list(
            filter(
                lambda p: has_suffix_among(p, [JSON_SUFFIX, JSON_GZ_SUFFIX]),
                files
            )
        )

        keyword2value_stat = dict()
        for f in files:
            f = self.file_service.open(f)
            lines = f.readlines()
            objs = filter(
                lambda o: o['result'] != '{}',
                [json.loads(j) for j in lines]
            )

            for o in objs:
                keyword2value_stat[o['keyword']] = []
                result_o = json.loads(o['result'])
                for feat in result_o["feature_stat"]:
                    if feat['value_type'] == stat_type:
                        keyword2value_stat[o['keyword']].append({
                            'feature_type': feat['feature_type'],
                            'value': feat['value']
                        })

        print(keyword2value_stat['아이돈띵쏘'])
        print(keyword2value_stat['콩 에센스'])
        assert len(keyword2value_stat['아이돈띵쏘']) > 0
        assert len(keyword2value_stat['콩 에센스']) > 0