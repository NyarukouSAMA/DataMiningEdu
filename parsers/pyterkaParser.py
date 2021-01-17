from enum import Enum

from parsers.baseParser import BaseParser
from enums.pyterka import *

class PyterkaParser(BaseParser):
    _params = {
        'records_per_page': 50,
    }

    def __init__(self, startUrl):
        super().__init__(startUrl)

    def run(self, fileName: PyterkaParserNames = PyterkaParserNames.productsId):
        for products in self.parse():
            for product in products:
                self._saveToJsonFile(product, product[fileName.value])
    
    def parse(self):
        url = self.startUrl
        params = self._params
        while url:
            response = self._get(url, params=params, headers=self._headers)
            if params:
                params = {}
            data: dict = response.json()
            url = data.get('next')
            yield data.get('results')
    

class PyterkaCatalogParser(PyterkaParser):
    def __init__(self, startUrl, categoryUrl):
        self.categoryUrl = categoryUrl
        super().__init__(startUrl)

    def parse(self):
        response = self._get(self.categoryUrl, headers=self._headers)
        for category in response.json():
            data = {
                'name': category['parent_group_name'],
                'code': category['parent_group_code'],
                'products': []
            }
            
            self._params['categories'] = data.get('code')
            for products in super().parse():
                data["products"].extend(products)
            
            yield data
    
    def run(self, fileName: CatalogParserNames = CatalogParserNames.categoryCode):
        for data in self.parse():
            self._saveToJsonFile(
                data,
                data.get(fileName.value)
            )