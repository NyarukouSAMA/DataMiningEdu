import scrapy
from scrapy import Selector
import re
import pymongo

class AutoyoulaSpider(scrapy.Spider):

    def __init__(self,  connectionString, collectionName, **kwargs):
        super().__init__(name=self.name, **kwargs)
        self.db = pymongo.MongoClient(connectionString)[collectionName]

    name = 'autoyoula'
    allowed_domains = ['auto.youla.ru']
    start_urls = ['http://auto.youla.ru/']

    css_query = {
        'brands': 'div.TransportMainFilters_block__3etab a.blackLink',
        'pagination': 'div.Paginator_block__2XAPy a.Paginator_button__u1e7D',
        'ads': 'article.SerpSnippet_snippet__3O1t2 a.SerpSnippet_name__3F7Yu',
    }

    data_query = {
        'title': lambda resp: resp.css('div.AdvertCard_advertTitle__1S1Ak::text').get(),
        'price': lambda resp: float(resp.css('div.AdvertCard_price__3dDCr::text').get().replace('\u2009', '')),
        'photos': lambda resp: [imageLink for imageLink in AutoyoulaSpider._get_image_list(resp)],
        'car_specs': lambda resp: AutoyoulaSpider._get_specs(resp),
        'desc': lambda resp: resp.css('div.AdvertCard_descriptionInner__KnuRi::text').get(),
        'author_href': lambda resp: resp.css('div.SellerInfo_block__1HmkE a.SellerInfo_name__3Iz2N')# .attrib['href'] #пока unlucky
    }

    @staticmethod
    def _get_image_list(resp):
        link = r'background-image:url\(([\W\w]+)\)'
        for urlContained in [img_selector.attrib['style'] for img_selector in resp.css('div.PhotoGallery_block__1ejQ1 button.PhotoGallery_thumbnailItem__UmhLO')]:
            yield re.findall(link, urlContained)[0]

    @staticmethod
    def _get_specs(resp):
        result = {}
        for spec_node in resp.css('div.AdvertCard_specs__2FEHc div.AdvertSpecs_row__ljPcX'):
            innerSellector = Selector(text=spec_node.getall()[0])
            key = innerSellector.css('.AdvertSpecs_label__2JHnS::text').get()
            value = innerSellector.css('.AdvertSpecs_data__xK2Qx ::text').get()
            result[key] = value
        return result

    def parse(self, response, **kwargs):
        brands_links = response.css(self.css_query['brands'])
        yield from self.gen_task(response, brands_links, self.brand_parse)

    def brand_parse(self, response):
        pagination_links = response.css(self.css_query['pagination'])
        yield from self.gen_task(response, pagination_links, self.brand_parse)
        ads_links = response.css(self.css_query['ads'])
        yield from self.gen_task(response, ads_links, self.ads_parse)

    def ads_parse(self, response):
        data = {}
        for key, selector in self.data_query.items():
            try:
                data[key] = selector(response)
            except (ValueError, AttributeError):
                continue
        self.save(data)

    @staticmethod
    def gen_task(response, link_list, callback):
        for link in link_list:
            yield response.follow(link.attrib['href'], callback=callback)

    def save(self, data):
        collection = self.db[self.name]
        collection.insert_one(data)
