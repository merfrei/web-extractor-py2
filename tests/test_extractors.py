import os
import unittest
from extractors.semantic import SemanticData, SemanticDS
from extractors.html import XPathExtractor


HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, 'data')


def get_file_content(filename):
    content = ''
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path) as f:
            content = f.read()
    return content


class TestSemantic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._html = get_file_content('page.html')
        cls._sd = SemanticData(cls._html)

    def test_data(self):
        self.assertIn('microdata', self._sd)
        self.assertTrue(self._sd['microdata'])
        self.assertIn('opengraph', self._sd)
        self.assertTrue(self._sd['opengraph'])
        self.assertIn('jsonld', self._sd)
        self.assertTrue(self._sd['jsonld'])

    def test_selectors(self):
        jsonld_selectors = {
            'product.name': 'Product.name',
            'product.image': 'Product.image',
        }
        microdata_selectors = {
            'product.category': 'BreadcrumbList.ListItem[-1].name',
        }
        sds = SemanticDS(jsonld_selectors)
        sds.select_data(self._sd['jsonld'])
        sds.selectors = microdata_selectors
        sds.select_data(self._sd['microdata'], False)
        result = sds.result
        self.assertEqual(result['product.name'], 'BePureHome Obvious Tafellamp')
        self.assertEqual(
            result['product.image'],
            'https://mb.fcdn.nl/square340/694344/bepurehome-obvious-tafellamp.jpg')
        self.assertEqual(result['product.category'], 'Tafellamp')

    def test_selector_from_value(self):
        selectors = [
            ('jsonld',
             'Product.name',
             'BePureHome Obvious Tafellamp'),
            ('jsonld',
             'Product.image',
             'https://mb.fcdn.nl/square340/694344/bepurehome-obvious-tafellamp.jpg'),
            ('microdata',
             'BreadcrumbList.ListItem[2].name',
             'Tafellamp'),
        ]
        for k, s, v in selectors:
            r = []
            SemanticDS.detect_from_value(self._sd[k], v, r)
            self.assertEqual(r[0], s)

    def test_master_path(self):
        paths = ['BreadcrumbList.ListItem[0].name',
                 'BreadcrumbList.ListItem[1].name']
        master_path = SemanticDS.detect_master_path(*paths)
        self.assertEqual(master_path, 'BreadcrumbList.ListItem.name')


class TestXpath(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._html = get_file_content('page.html')
        cls._xpe = XPathExtractor(cls._html)

    def test_extract(self):
        xpath = '//div[@id="productpage-container"]//h1/text()'
        v = self._xpe.extract(xpath)[0]
        self.assertEqual(v, 'BePureHome Obvious Tafellamp')

    def test_extract_text(self):
        xpath = '//div[@id="productpage-container"]//h1'
        v = self._xpe.extract_text(xpath)[0]
        self.assertEqual(v, 'BePureHome Obvious Tafellamp')

    def test_from_value(self):
        v1 = 'BePureHome Obvious Tafellamp'
        xpath = self._xpe.get_xpath_from_value(v1)
        v2 = self._xpe.extract_text(xpath[0])[0]
        self.assertEqual(v1, v2)

    def test_from_values(self):
        values = ['Wonen', 'Tuin & Vrije Tijd']
        master_path = self._xpe.get_xpath_from_value(*values)
        all_values = self._xpe.extract_text(master_path)
        self.assertEqual(all_values, ['Wonen', 'Tuin & Vrije Tijd',
                                      'Koken & Tafelen',
                                      'Lifestyle', 'Huishouden',
                                      'Body & Sport', 'Baby & Kids'])


if __name__ == '__main__':
    unittest.main()
