import requests
from requests.models import Response
from datetime import datetime
import bs4
import json
import time

from sqlalchemy.sql.expression import select

class BaseParser:
    _params: dict
    _headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0',
    }
    _statusSuccess = [200]

    def __init__(self, startUrl):
        self.startUrl = startUrl
    
    @classmethod
    def _get(self, *args, **kwargs):
        while True:
            try:
                response = requests.get(*args, **kwargs)
                if response.status_code not in self._statusSuccess:
                    raise Exception(response) # todo сделать класс ошибки для работы со статусами
                time.sleep(0.1)
                return response
            except Exception as ex:
                errorDT = datetime.now()
                exData = {
                    'datetime': errorDT.isoformat()
                }
                for arg in ex.args:
                    if type(arg) is Response:
                        exData['exReason'] = 'Request Error'
                        exData['status'] = arg.status_code
                        exData['responceObject'] = arg.__dict__
                        break
                if 'exReason' not in exData:
                    exData['exReason'] = 'Another Error'
                self._saveToJsonFile(exData, f'error_{errorDT:%Y%m%d}', 'requestErrorLog')
                time.sleep(60)

    @classmethod
    def _saveToJsonFile(self, data: dict, fileName, dirName = 'products'):
        with open(f'{dirName}/{fileName}.json', 'w', encoding='UTF-8') as file:
            json.dump(data, file, ensure_ascii=False)

    @classmethod
    def _saveToTxtFile(self, data: str, fileName, dirName = 'products'):
        with open(f'{dirName}/{fileName}.txt', 'w', encoding='UTF-8') as file:
            file.write(data.encode('utf8'))

    @classmethod
    def _getSoup(self, *args, **kwargs):
        response = requests.get(*args, **kwargs)
        soup = bs4.BeautifulSoup(response.text, 'lxml')
        return soup