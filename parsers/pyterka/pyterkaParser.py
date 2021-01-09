from enum import Enum
import json
import requests
import time
from datetime import datetime
from requests.models import Response

from enums.pyterka import PyterkaParserNames

class PyterkaParser:
    _params = {
        'records_per_page': 50,
    }
    _headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0',
    }
    fileNames: Enum
    
    def __init__(self, start_url):
        self.start_url = start_url
    
    @staticmethod
    def _get(*args, **kwargs):
        while True:
            try:
                response = requests.get(*args, **kwargs)
                if response.status_code != 200:
                    raise Exception(response) # todo сделать класс ошибки для работы со статусами
                time.sleep(0.1)
                return response
            except Exception as ex:
                errorDT = datetime.now()
                exData = {
                    'datetime': errorDT
                }
                for arg in ex.args:
                    if type(arg) is Response:
                        exData['exReason'] = 'Request Error'
                        exData['status'] = arg.status
                        exData['responceObject'] = arg.__dict__
                        break
                if 'exReason' not in exData:
                    exData['exReason'] = 'Another Error'
                PyterkaParser.save_to_json_file(exData, f'error_{errorDT:%Y%m%d}', 'requestErrorLog')
                time.sleep(60)
    
    def run(self, fileName: PyterkaParserNames = PyterkaParserNames.productsId):
        for products in self.parse():
            for product in products:
                self.save_to_json_file(product, product[fileName.value])
    
    def parse(self):
        url = self.start_url
        params = self._params
        while url:
            response = self._get(url, params=params, headers=self._headers)
            if params:
                params = {}
            data: dict = response.json()
            url = data.get('next')
            
            yield data.get('results')
    
    @staticmethod
    def save_to_json_file(data: dict, file_name, dir_name = 'products'):
        with open(f'{dir_name}/{file_name}.json', 'w', encoding='UTF-8') as file:
            json.dump(data, file, ensure_ascii=False)