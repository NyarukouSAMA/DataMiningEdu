import requests
from requests.models import Response
from datetime import datetime
import bs4
import json
import time

class BaseParser:
    __params: dict
    __headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0',
    }

    def __init__(self, startUrl):
        self.startUrl = startUrl
    
    @staticmethod
    def __get(*args, **kwargs):
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
                BaseParser.__saveToJsonFile(exData, f'error_{errorDT:%Y%m%d}', 'requestErrorLog')
                time.sleep(60)

    @staticmethod
    def __saveToJsonFile(data: dict, fileName, dirName = 'products'):
        with open(f'{dirName}/{fileName}.json', 'w', encoding='UTF-8') as file:
            json.dump(data, file, ensure_ascii=False)

    @staticmethod
    def __getSoup(self, *args, **kwargs):
        response = requests.get(*args, **kwargs)
        soup = bs4.BeautifulSoup(response.text, 'lxml')
        return soup