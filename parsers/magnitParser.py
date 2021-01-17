from parsers.baseParser import BaseParser
import bs4
import re
from urllib.parse import urljoin
import pymongo
from datetime import datetime


class MagnitParse(BaseParser):
    __monthDict = {
        'янв': 1,
        'фев': 2,
        'мар': 3,
        'апр': 4,
        'мая': 5,
        'июн': 6,
        'июл': 7,
        'авг': 8,
        'сен': 9,
        'окт': 10,
        'ноя': 11,
        'дек': 12,
    }

    __fromDatePat = r'\w*\s?(\d{1,2}\s\w+)\W\w*\s?\w*'
    __toDatePat = r'\w*\s?\d{1,2}\s\w+\W\w*\s?(\d{1,2}\s\w+)'

    def __init__(self, startUrl, connectionString, collectionName):
        super.__init__(startUrl)
        self.db = pymongo.MongoClient(connectionString)[collectionName]

    def run(self):
        for product in self.parse():
            self.save(product)

    def parse(self):
        soup = self._getSoup(self.startUrl)
        catalogMain = soup.find('div', attrs={'class': 'сatalogue__main'})
        for productTag in catalogMain.find_all('a', recursive=False):
            try:
                yield self.productParse(productTag)
            except AttributeError as ex:
                for arg in ex.args:
                    print(arg)

    def productParse(self, product: bs4.Tag) -> dict:
        period = self.__getPeriod(product.find('div', attrs={'class': 'card-sale__date'}))
        old_price_tag = product.find('div', attrs={'class': 'label__price label__price_old'})
        new_price_tag = product.find('div', attrs={'class': 'label__price label__price_new'})
        product = {
            'url': urljoin(self.start_url, product.get('href')),
            'promo_name': product.find('div', attrs={'class': 'card-sale__name'}).text if product.find('div', attrs={'class': 'card-sale__name'}) else None,
            'product_name': product.find('div', attrs={'class': 'card-sale__title'}).text,
            'old_price': self.__getPrice(old_price_tag) if old_price_tag is not None else None,
            'new_price': self.__getPrice(new_price_tag) if new_price_tag is not None else None,
            'image_url': urljoin(self.start_url, product.find('img').get('data-src') if product.find('img') else None),
            'date_from': period['date_from'],
            'date_to': period['date_to']
        }
        return product

    def __getPrice(self, price: bs4.Tag) -> float:
        intPartTag = price.find('span', attrs={'class': 'label__price-integer'})
        if intPartTag is not None:
            intPartTry = self.__intTryParse(intPartTag.text)
            intPart = intPartTry[0] if intPartTry[1] else None
        else:
            intPart = None
        floatPartTag = price.find('span', attrs={'class': 'label__price-decimal'})
        floatPart = floatPartTag.text if intPart is not None and floatPartTag is not None else None
        return float(f'{intPart}.{floatPart if floatPart is not None else 0}') if intPart is not None else None

    def __getPeriod(self, period: bs4.Tag) -> dict:
        fromPartList = None
        toPartList = None
        fromPartSearchR = re.findall(self.__fromDatePat, period.text)
        fromPart = fromPartSearchR[0].split(' ') if len(fromPartSearchR) > 0 else None
        if fromPart is not None:
            fromPartList = [int(fromPart[0]), self.__monthDict.get(fromPart[1][:3])]
        toPartSearchR = re.findall(self.__toDatePat, period.text)
        toPart = toPartSearchR[0].split(' ') if len(toPartSearchR) > 0 else None
        if toPart is not None:
            toPartList = [int(toPart[0]), self.__monthDict.get(toPart[1][:3])]
        currentYear = datetime.now().year
        currentMonth = datetime.now().month
        
        if fromPartList is None or toPartList is None:
            return {
                'date_from': datetime(currentYear, fromPartList[1], fromPartList[0]) if fromPartList is not None else None,
                'date_to': datetime(currentYear, toPartList[1], toPartList[0]) if toPartList is not None else None
            }
        else:
            if fromPartList[1] > toPartList[1]:
                if currentMonth <= toPartList[1]:
                    period = {
                        'date_from': datetime(currentYear - 1, fromPartList[1], fromPartList[0]),
                        'date_to': datetime(currentYear, toPartList[1], toPartList[0])
                    }
                else:
                    period = {
                        'date_from': datetime(currentYear, fromPartList[1], fromPartList[0]),
                        'date_to': datetime(currentYear + 1, toPartList[1], toPartList[0])
                    }
            else:
                period = {
                    'date_from': datetime(currentYear, fromPartList[1], fromPartList[0]),
                    'date_to': datetime(currentYear, toPartList[1], toPartList[0])
                }
        
        return period
        
    def __intTryParse(self, value):
        try:
            return int(value), True
        except ValueError:
            return value, False

    def save(self, data):
        collection = self.db['magnit']
        collection.insert_one(data)
        print(1)