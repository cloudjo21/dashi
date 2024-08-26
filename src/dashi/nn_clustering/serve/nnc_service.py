import nltk
import numpy as np
import re

from pydantic import BaseModel
from sklearn.feature_extraction.text import CountVectorizer

from tunip.nugget_api import Nugget, NuggetFilterResultFormat
from tunip.Hangulpy import is_hangul

from tweak.clustering import NncRequest
from tweak.clustering.distance.bigram_jaccard_dist import (
    BigramJaccardDistanceCalc,
    JaccardDistanceCalcRequest,
    JaccardDistanceCalcResponse
)
from tweak.clustering.factory import NncFactory
from tweak.clustering.hac import HAC

from dashi import LOGGER
from dashi.utils.deploys import NncServiceDeploy


class SimpleSearchResult(BaseModel):
    title: str
    docid: int


class NncTask:
    pass

class HACTask(NncTask):
    def __init__(self, model: HAC, max_row: int):
        self.nugget = Nugget()
        self.white_ptags = {
            'unigram': ['V', 'N', 'SL', 'SH', 'SN'],
            'bigram': ['V', 'N', 'J', 'M', 'SL', 'SH', 'SN'],
            # ['V', 'N', 'M', 'SL', 'SH', 'SN'],
        }

        self.regex_normalize_nums = re.compile('\d+')

        self.distance_calc = BigramJaccardDistanceCalc()
        self.model = model

        self.max_row = max_row


    def analyze(self, es_result):

        titles = []
        titles_unigram = []
        es_doc_ids = []

        es_doc_ids_wo_titlenugget = []
        for idx, row in enumerate(es_result['hits']['hits']):
            if 'titlenugget' in row['_source']:
                title_normed: list = self._preprocess_for_title(row['_source']['titlenugget']).split(' ')
                titles_unigram.append(list(set(title_normed)))
                titles.append(nltk.bigrams(title_normed))
            else:
                LOGGER.warning(f"there is no titlenugget field for this article: {row['_source']['title']}")
                title_normed: str = self._preprocess_for_title(row['_source']['title'])
                es_doc_ids_wo_titlenugget.append((idx, title_normed))
                titles_unigram.append([])
                titles.append([])

            es_doc_ids.append(row['_id'])
        
        # request bigrams to nugget for NOT-indexed titles
        raw_titles = [e[1] for e in es_doc_ids_wo_titlenugget]
        bigram_tokens_list_wo_titlenugget, unigram_tokens_list = self.nugget.bigrams_also_selective_tags(
            raw_titles, white_tags_dict=self.white_ptags
        )

        for idx, (unigrams, bigrams) in enumerate(zip(unigram_tokens_list, bigram_tokens_list_wo_titlenugget)):
            titles_unigram[es_doc_ids_wo_titlenugget[idx][0]] = unigrams
            titles[es_doc_ids_wo_titlenugget[idx][0]] = bigrams

        corpus = []
        for unigrams, bigrams in zip(titles_unigram, titles):
            corpus.append(f"{' '.join(unigrams)} {' '.join(map('_'.join, bigrams))}")

        term_vector = self._get_term_vector(corpus)

        # max_row is set by deploy config
        dist_calc_req = JaccardDistanceCalcRequest(term_vector= term_vector, num_rows=self.max_row)
        dist_calc_res: JaccardDistanceCalcResponse = self.distance_calc(dist_calc_req)
        nnc_req = NncRequest(
            distances=dist_calc_res.distances,
            dist_calc_status=dist_calc_res.status,
            method='average'
        )

        # docid_clusters
        docid_clusters = self.model(nnc_req)

        return docid_clusters, es_doc_ids
    
    def _get_term_vector(self, corpus):
        if not corpus:
            return np.ndarray([0], dtype=np.int8)
        vectorizer = CountVectorizer()

        # scipy.sparse._csr.csr_matrix
        xx = vectorizer.fit_transform(corpus)

        # numpy.ndarray
        return xx.toarray()

    def _preprocess_for_title(self, text):
        text = self.regex_normalize_nums.sub('0', text)
        text = ' '.join(map(lambda w: ''.join(filter(lambda c: c.isdigit() or is_hangul(c), w)), text.split(' ')))
        text = re.sub('  ', ' ', text)
        return text


class NncService:
    """
    Nearest Neighborhood Clustering Service
    """
    def __init__(self, deploy: NncServiceDeploy):
        self.task = HACTask(
            model=NncFactory.create(deploy.model_name, deploy.distance_threshold),
            max_row=deploy.es_search_result_size
        )

    def collapse_search(self, es_result):
        docid_clusters, es_doc_ids = self.task.analyze(es_result)
        es_result_collapse, es_result_rest = self._collapse_es_result(docid_clusters, es_doc_ids, es_result)
        return es_result_collapse, es_result_rest


    def collapse_search_for_docids(self, es_result):
        docid_clusters, es_doc_ids = self.task.analyze(es_result)
        es_result_collapse, es_result_rest = self._coallpse_docids(docid_clusters, es_doc_ids, es_result)
        return es_result_collapse, es_result_rest


    def _coallpse_docids(self, docid_clusters, es_doc_ids, es_result):
        es_result_collapse = []
        es_doc_ids_collapse = []
        for doc_ids in docid_clusters:
            cluster_doc_ids = [es_doc_ids[id] for id in doc_ids]
            es_doc_ids_collapse.extend(cluster_doc_ids)

            cluster_result = [{'_id': r['_id']} for r in es_result['hits']['hits'] if r['_id'] in cluster_doc_ids]
            cluster_result[0]["inner_hits"] = {
                "hits": {
                    "hits": cluster_result[1:]  # [r['_id'] for r in cluster_result[1:]]
                }
            }
            es_result_collapse.append(cluster_result[0])
        es_result_rest = [{'_id': r['_id'], 'inner_hits': {}} for r in es_result['hits']['hits'] if r['_id'] not in es_doc_ids_collapse]
        return es_result_collapse, es_result_rest


    def _collapse_es_result(self, docid_clusters, es_doc_ids, es_result):
        es_result_collapse = []
        es_doc_ids_collapse = []
        for doc_ids in docid_clusters:
            cluster_doc_ids = [es_doc_ids[id] for id in doc_ids]
            es_doc_ids_collapse.extend(cluster_doc_ids)

            cluster_result = [r for r in es_result['hits']['hits'] if r['_id'] in cluster_doc_ids]
            cluster_result[0]["inner_hits"] = {
                "hits": {
                    "hits": cluster_result[1:]
                }
            }
            es_result_collapse.append(cluster_result[0])
        es_result_rest = [r for r in es_result['hits']['hits'] if r['_id'] not in es_doc_ids_collapse]

        # print(f'es_result_collapse ({len(es_result_collapse)}):')
        # for e in es_result_collapse:
        #     print(f"{e['_id']} : {e['_source']['title']}")
        #     for ei in e['inner_hits']['hits']['hits']:
        #         print(f"\t{ei['_id']} : {ei['_source']['title']}")
        # print(f'es_result_rest ({len(es_result_rest)}):')
        # print([f"{e['_id']} : {e['_source']['title']}" for e in es_result_rest[0:2]])

        return es_result_collapse, es_result_rest
