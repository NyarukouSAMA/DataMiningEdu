from parsers.magnitParser import MagnitParse

parser = MagnitParse("https://magnit.ru/promo/?geo=moskva", 'mongodb://localhost:27017', 'gb_parse_12')
parser.run()