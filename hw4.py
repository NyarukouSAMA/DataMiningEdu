from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from gbParse.spiders.autoyoula import AutoyoulaSpider

if __name__ == '__main__':
    crawler_settings = Settings()
    crawler_settings.setmodule('gbParse.settings')
    crawler_process = CrawlerProcess(settings=crawler_settings)
    crawler_process.crawl(AutoyoulaSpider, 'mongodb://localhost:27017', 'gb_parse_12')
    crawler_process.start()