from enums.pyterka import CatalogParserNames
from .pyterkaParser import PyterkaParser

class PyterkaCatalogParser(PyterkaParser):
    def __init__(self, start_url, category_url):
        self.category_url = category_url
        super().__init__(start_url)

    def parse(self):
        response = self._get(self.category_url, headers=self._headers)
        for category in response.json():
            data = {
                'name': category['parent_group_name'],
                'code': category['parent_group_code'],
                'products': []
            }
            
            self._params['categories'] = data.get('code')
            for products in super().parse():
                data["products"].extend(products)
            
            yield data
    
    def run(self, fileName: CatalogParserNames = CatalogParserNames.categoryCode):
        for data in self.parse():
            self.save_to_json_file(
                data,
                data.get(fileName.value)
            )