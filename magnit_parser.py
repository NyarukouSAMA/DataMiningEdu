import requests
import bs4
import re
from urllib.parse import urljoin
import pymongo
from datetime import datetime


class MagnitParse:
    __month_dict = {
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

    __from_date_pat = r'\w*\s?(\d{1,2}\s\w+)\W\w*\s?\w*'
    __to_date_pat = r'\w*\s?\d{1,2}\s\w+\W\w*\s?(\d{1,2}\s\w+)'

    def __init__(self, start_url, mongo_db):
        self.start_url = start_url
        self.db = mongo_db

    def __get_soup(self, url) -> bs4.BeautifulSoup:
        # todo предусмотреть внештатные ситуации
        response = requests.get(url)
        return bs4.BeautifulSoup(response.text, 'lxml')

    def run(self):
        for product in self.parse():
            self.save(product)

    def parse(self):
        soup = self.__get_soup(self.start_url)
        catalog_main = soup.find('div', attrs={'class': 'сatalogue__main'})
        for product_tag in catalog_main.find_all('a', recursive=False):
            try:
                yield self.product_parse(product_tag)
            except AttributeError as ex:
                for arg in ex.args:
                    print(arg)

    def product_parse(self, product: bs4.Tag) -> dict:
        period = self.__get_period(product.find('div', attrs={'class': 'card-sale__date'}))
        old_price_tag = product.find('div', attrs={'class': 'label__price label__price_old'})
        new_price_tag = product.find('div', attrs={'class': 'label__price label__price_new'})
        product = {
            'url': urljoin(self.start_url, product.get('href')),
            'promo_name': product.find('div', attrs={'class': 'card-sale__name'}).text if product.find('div', attrs={'class': 'card-sale__name'}) else None,
            'product_name': product.find('div', attrs={'class': 'card-sale__title'}).text,
            'old_price': self.__get_price(old_price_tag) if old_price_tag is not None else None,
            'new_price': self.__get_price(new_price_tag) if new_price_tag is not None else None,
            'image_url': urljoin(self.start_url, product.find('img').get('data-src') if product.find('img') else None),
            'date_from': period['date_from'],
            'date_to': period['date_to']
        }
        return product

    def __get_price(self, price: bs4.Tag) -> float:
        int_part_tag = price.find('span', attrs={'class': 'label__price-integer'})
        if int_part_tag is not None:
            int_part_try = self.__int_try_parse(int_part_tag.text)
            int_part = int_part_try[0] if int_part_try[1] else None
        else:
            int_part = None
        float_part_tag = price.find('span', attrs={'class': 'label__price-decimal'})
        float_part = float_part_tag.text if int_part is not None and float_part_tag is not None else None
        return float(f'{int_part}.{float_part if float_part is not None else 0}') if int_part is not None else None

    def __get_period(self, period: bs4.Tag) -> dict:
        from_part_list = None
        to_part_list = None
        from_part_search_r = re.findall(self.__from_date_pat, period.text)
        from_part = from_part_search_r[0].split(' ') if len(from_part_search_r) > 0 else None
        if from_part is not None:
            from_part_list = [int(from_part[0]), self.__month_dict.get(from_part[1][:3])]
        to_part_search_r = re.findall(self.__to_date_pat, period.text)
        to_part = to_part_search_r[0].split(' ') if len(to_part_search_r) > 0 else None
        if to_part is not None:
            to_part_list = [int(to_part[0]), self.__month_dict.get(to_part[1][:3])]
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        if from_part_list is None or to_part_list is None:
            return {
                'date_from': datetime(current_year, from_part_list[1], from_part_list[0]) if from_part_list is not None else None,
                'date_to': datetime(current_year, to_part_list[1], to_part_list[0]) if to_part_list is not None else None
            }
        else:
            if from_part_list[1] > to_part_list[1]:
                if current_month <= to_part_list[1]:
                    period = {
                        'date_from': datetime(current_year - 1, from_part_list[1], from_part_list[0]),
                        'date_to': datetime(current_year, to_part_list[1], to_part_list[0])
                    }
                else:
                    period = {
                        'date_from': datetime(current_year, from_part_list[1], from_part_list[0]),
                        'date_to': datetime(current_year + 1, to_part_list[1], to_part_list[0])
                    }
            else:
                period = {
                    'date_from': datetime(current_year, from_part_list[1], from_part_list[0]),
                    'date_to': datetime(current_year, to_part_list[1], to_part_list[0])
                }
        
        return period
        
    def __int_try_parse(self, value):
        try:
            return int(value), True
        except ValueError:
            return value, False

    def save(self, data):
        collection = self.db['magnit']
        collection.insert_one(data)
        print(1)


if __name__ == '__main__':
    database = pymongo.MongoClient('mongodb://localhost:27017')['gb_parse_12']
    parser = MagnitParse("https://magnit.ru/promo/?geo=moskva", database)
    parser.run()
