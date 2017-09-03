"""Semantic Data Selection & Extraction Utilities
- Semantic data extraction from HTML using extruct library
- Cleaning and reformatting the extruct library output to easily parse the content
- Using semantic data selectors (with an object notation type) to extract the data"""

import re
import requests
import extruct
from extractors.utils import get_master_path


class SemanticDataBase(object):
    """Semantic Data Base
    Implements __init__, __getitem__ and _init_data methods
    Methods that should never be overriden"""

    def __init__(self, html, url=''):
        self._url = url
        self._original = extruct.extract(html, url)
        self._init_data()

    def __getitem__(self, key):
        return self._data[key]

    def __contains__(self, key):
        return (key in self._data)

    def _init_data(self):
        self._data = {}
        for k, c in self._parsing_methods():
            self._data[k] = c[0](self._original[c[1]])

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def values(self):
        return self._data.values()

    @classmethod
    def from_url(self, cls, url):
        """
        Allows to create a new instance from a given URL
        It gets the resource, create and returns a new SemanticData object
        """
        res = requests.get(url)
        return cls(res.text, url)

    def _parsing_methods(self):
        """
        It's used to get specific data from the base data (extruct)
        building the _data property for the SemanticData instance
        Iterable to be used into `_init_data()` method
        You can build custom SemanticData objects by implementing this method
        It should return tuples with the following format:
        (my_data_key, (callback, extruct_result_key))
        ie: ('opengraph', (self._parse_rdfa_opengraph, 'rdfa'))
        """
        raise NotImplementedError('_parsing_methods must be implemented')


class SemanticData(SemanticDataBase):
    """Default Semantic Data object
    """

    def _parsing_methods(self):
        cbcks = [
            ('microdata', (SemanticDataUtils.parse_microdata, 'microdata')),
            ('opengraph', (SemanticDataUtils.parse_rdfa_opengraph, 'rdfa')),
            ('jsonld', (SemanticDataUtils.parse_jsonld_schema_org, 'json-ld')),
        ]
        for k, c in cbcks:
            yield k, c


class SemanticDataUtils(object):
    """Semantic Data Utils
    Methods to be used by the parsing function in SemanticData
    """

    @classmethod
    def parse_microdata(cls, data):
        def get_key(t):
            return re.search(r'\.org\/(\w+)/?|$', t).group(1) or t
        microdata = {}
        if isinstance(data, list):
            for d in data:
                k = get_key(d['type'])
                v = cls.parse_microdata(d['properties'])
                if k in microdata:
                    if isinstance(microdata[k], list):
                        microdata[k].append(v)
                    else:
                        microdata[k] = [microdata[k]] + [v]
                else:
                    microdata[k] = v
        elif isinstance(data, dict):
            for k_, v in data.items():
                if isinstance(v, dict) and ('type' in v):
                    k = get_key(v['type'])
                    microdata[k] = cls.parse_microdata(v['properties'])
                elif isinstance(v, list):
                    microdata.update(cls.parse_microdata(v))
                else:
                    microdata[k_] = v
        else:
            microdata = data
        return microdata

    @staticmethod
    def parse_rdfa_opengraph(rdfa):
        ogp = {}
        for d in rdfa:
            if any('ogp.me/ns' in k for k in d.keys()):
                for k, v in d.items():
                    if not v:
                        continue
                    if not isinstance(v, list):
                        continue
                    if '@value' not in v[0]:
                        continue
                    prop = re.search(r'ogp.me/ns/?(.*)|$', k).group(1)
                    if not prop:
                        continue
                    prop = prop.replace('#', ':')
                    prop = 'og' + prop if prop.startswith(':') else prop
                    ogp[prop] = v[0]['@value']
        return ogp

    @staticmethod
    def parse_jsonld_schema_org(jld):
        sorg = {}
        for d in jld:
            if 'schema.org' in d.get('@context', ''):
                # I'm using `in` to avoid issues resulting from different variants
                # ie: http://... and https://... or ...schema.org/ and ...schema.org
                k = d.get('@type')
                if not k:
                    continue
                sorg[k] = {}
                for k_, v in d.items():
                    if k_.startswith('@') and k_ != '@id':
                        continue
                    sorg[k][k_] = v
        return sorg


class SemanticDS(object):
    """Semantic Data Selector
    Parses SemanticData using selectors and returns the result"""

    def __init__(self, selectors):
        """
        `selectors` should be a dict with the following format:
            result key => selector
        """
        self._selectors = selectors
        self._build_parser()
        self._result = {}

    def _build_parser(self):
        """Parser Graph example:
            {
              "Breadcrumb": {
                "$index": -1,
                "title": {
                  "$result": "product.category"
                }
              },
              "Product": {
                "Offer": {
                  "$result": "product.offers"
                },
                "name": {
                  "$result": "product.name"
                }
              }
            }
        """
        self._parser = {}
        selectors = self._selectors
        for s in selectors:
            if not selectors[s]:
                continue
            path_ = selectors[s].split('.')
            curr_ = self._parser
            for r in path_:
                if not(r in curr_):
                    curr_[r] = {}
                curr_ = curr_[r]
            curr_['$result'] = s

    def select_data(self, data, clean=True):
        if clean:
            self.clean_result()
        self._select_data(data)

    def _select_data(self, data, parser=None):
        if not data:
            return
        if parser is None:
            parser = self._parser
        result = self._result
        data_ = data
        if '$result' in parser:
            rk_ = parser['$result']
            if rk_ in result:
                if isinstance(result[rk_], list):
                    result[rk_].append(data_)
                else:
                    result[rk_] = [result[rk_]] + [data_]
            else:
                result[rk_] = data_
        for p in parser:
            if p.startswith('$'):
                continue
            p_, ix = re.search(r'^(.*)\[(-?\d+)\]$|$', p).groups()
            if ix:
                if p_ in data_:
                    self._select_data(data_[p_][int(ix)], parser[p])
                else:
                    # No data found: force to finish
                    self._select_data(None, parser[p])
            elif isinstance(data_, list):  # Master Path support added
                for d in data_:
                    self._select_data(d.get(p), parser[p])
            else:
                self._select_data(data_.get(p), parser[p])

    @property
    def result(self):
        return self._result.copy()

    def clean_result(self):
        self._result = {}

    @property
    def selectors(self):
        return self._selectors.copy()

    @selectors.setter
    def selectors(self, new_selectors):
        self._selectors = new_selectors
        self._build_parser()

    def update_selectors(self, selectors):
        self._selectors.update(selectors)
        self._build_parser()

    @classmethod
    def detect_from_value(cls, data, value, result, **kwargs):
        path = None
        if 'path' in kwargs:
            path = kwargs['path']
        if path is None:
            path = []
        if data == value:
            return '.'.join(path)
        if isinstance(data, list):
            for ix, data_ in enumerate(data):
                path_ = list(path)
                path_[-1] += '[%s]' % ix
                r = cls.detect_from_value(data_, value, result, path=path_)
                if r is not None:
                    result.append(r)
        elif isinstance(data, dict):
            for p in data:
                path_ = list(path)
                path_.append(p)
                r = cls.detect_from_value(data[p], value, result, path=path_)
                if r is not None:
                    result.append(r)

    @staticmethod
    def detect_master_path(*paths):
        return get_master_path(*paths, separator='.')
