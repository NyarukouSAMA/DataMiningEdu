from enum import Enum

from parsers.baseParser import BaseParser
from enums.pyterka import *

class PyterkaParser(BaseParser):
    __params = {
        'records_per_page': 50,
    }

    def __init__(self, startUrl):
        super().__init__(startUrl)

    def run(self, fileName: PyterkaParserNames = PyterkaParserNames.productsId):
        for products in self.parse():
            for product in products:
                self.__saveToJsonFile(product, product[fileName.value])
    
    def parse(self):
        url = self.startUrl
        params = self.__params
        while url:
            response = self.__get(url, params=params, headers=self.__headers)
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
        response = self.__get(self.categoryUrl, headers=self.__headers)
        for category in response.json():
            data = {
                'name': category['parent_group_name'],
                'code': category['parent_group_code'],
                'products': []
            }
            
            self.__params['categories'] = data.get('code')
            for products in super().parse():
                data["products"].extend(products)
            
            yield data
    
    def run(self, fileName: CatalogParserNames = CatalogParserNames.categoryCode):
        for data in self.parse():
            self.__saveToJsonFile(
                data,
                data.get(fileName.value)
            )