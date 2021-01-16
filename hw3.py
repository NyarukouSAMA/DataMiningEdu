import os
from dotenv import load_dotenv

from crud.gbDB import Database
from parsers.gbBlogParser import GbParse

load_dotenv('.env')
sql = os.getenv('SQL_DB')
parser = GbParse('https://geekbrains.ru/posts','https://geekbrains.ru/api/v2/comments',
                 Database(os.getenv('SQL_DB')))
parser.run()