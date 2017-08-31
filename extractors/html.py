"""HTML Extractor
Extractor service for parsing and extracting content from a webpage using selectors.
Here is all the main code to be used for that purpose."""

import requests
from lxml import html
from lxml import etree
from extractors.utils import get_master_path


class XPathExtractor(object):
    """Extractor class to extract data using XPath like selectors"""
    def __init__(self, html):
        self._html = html
        self._init_tree()

    def _init_tree(self):
        self._root = html.fromstring(self._html)
        self._tree = etree.ElementTree(self._root)

    def extract(self, xpath):
        return self._tree.xpath(xpath)

    def extract_text(self, xpath, strip=True):
        result = []
        for e in self._tree.xpath(xpath):
            if hasattr(e, 'text'):
                if strip:
                    result.append(e.text.strip())
                else:
                    result.append(e.text)
            else:
                result.append(e)
        return result

    def get_xpath_from_value(self, *values):
        extract_plist = []
        for t in values:
            try:
                results = []
                for e in self._tree.xpath('//*[contains(text(), "%s")]' % t):
                    if hasattr(e, 'text') and e.text is not None \
                       and t == e.text.strip():
                        results.append(e)
                extract_plist.extend([self._tree.getpath(r) for r in results])
            except IndexError:
                continue
        eplng = len(extract_plist)
        if len(values) > 1 and eplng > 1:
            return get_master_path(*extract_plist)
        return extract_plist

    @classmethod
    def from_url(cls, url):
        res = requests.get(url)
        return cls(res.text)
