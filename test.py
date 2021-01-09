from parsers.pyterka.pyterkaCatalogParser import PyterkaCatalogParser

parser = PyterkaCatalogParser('https://5ka.ru/api/v2/special_offers/', 'https://5ka.ru/api/v2/categories/')
parser.run()