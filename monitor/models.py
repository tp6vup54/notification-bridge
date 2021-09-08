import asyncio
import json
import urllib

import aiohttp
from bs4 import BeautifulSoup

from db.sqlite import Sqlite
import monitor


class Decathlon(monitor.Monitor):
    def __init__(self, db: Sqlite, path: str):
        super(Decathlon, self).__init__(db)
        self.fqdn = 'www.decathlon.tw'
        self.uri = urllib.parse.urljoin(f'https://{self.fqdn}', path)

    async def get_alert_text(self) -> str:
        histories = self.db.get_site_history(self.fqdn)
        async with aiohttp.ClientSession() as session:
            async with session.get(self.uri) as resp:
                html = await resp.text()
        soup = BeautifulSoup(html, 'lxml')
        products = soup.select('.products-grid > li')
        products_discounted = list(filter(self._is_discount, products))
        products_need_alert = list(filter(lambda x: self._is_not_sent_before(x, histories), products_discounted))
        self._purge_retired_histories(products_discounted, histories)
        self._insert_histories(products_need_alert)
        return ', '.join([self._generate_text(p) for p in products_need_alert])

    def _is_discount(self, product: BeautifulSoup) -> bool:
        return product.select_one('.special-price') is not None

    def _is_not_sent_before(self, product: BeautifulSoup, histories: [tuple]) -> bool:
        name = product.select_one('.product-name').text.strip()
        for h in histories:
            if name == h[1]:
                return False
        return True

    def _insert_histories(self, products: [BeautifulSoup]) -> None:
        self.db.insert_site_history([(p.select_one('.product-name').text.strip(), self.fqdn) for p in products])

    def _purge_retired_histories(self, products: [BeautifulSoup], histories: [tuple]) -> None:
        names = [p.select_one('.product-name').text.strip() for p in products]
        self.db.delete_site_history([h[0] for h in histories if h[1] not in names])

    def _generate_text(self, product: BeautifulSoup) -> str:
        name = product.select_one('.product-name').text.strip()
        price = product.select_one('.special-price').text.strip()
        href = product.select_one('.productimg > a').attrs['href']
        return f'item: [{name}]({href}) at price: {price}'


class Uniqlo(monitor.Monitor):
    def __init__(self, db: Sqlite, path: str):
        super(Uniqlo, self).__init__(db)
        self.fqdn = 'www.uniqlo.com'
        self.base_url = f'https://{self.fqdn}'
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'
        }
        self.uri = urllib.parse.urljoin(self.base_url, path)

    async def get_alert_text(self) -> str:
        histories = self.db.get_site_history(self.fqdn)
        product_codes = await self._get_product_codes()
        product_details = await asyncio.gather(*(self._get_product_details(c) for c in product_codes))
        products_discounted = list(filter(self._is_not_sold_out, filter(self._is_discount, product_details)))
        products_need_alert = list(filter(lambda x: self._is_not_sent_before(x, histories), products_discounted))
        self._purge_retired_histories(products_discounted, histories)
        self._insert_histories(products_need_alert)
        return ', '.join([self._generate_text(p) for p in products_need_alert])

    async def _get_product_codes(self) -> [str]:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.uri, headers=self.header) as resp:
                html = await resp.text()
        j = json.loads(html)
        codes = []
        for v in j.values():
            if v['component'] == 'ProductGroup':
                codes.extend([i['productCode'] for i in v['props']['items']])
        return codes

    async def _get_product_details(self, product_code: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self.base_url}/tw/data/products/prodInfo/zh_TW/{product_code}.json',
                                   headers=self.header) as resp:
                html = await resp.text()
        return json.loads(html)

    def _is_discount(self, product_detail: dict) -> bool:
        return product_detail['priceColor'] == 'red'

    def _is_not_sold_out(self, product_detail: dict) -> bool:
        return product_detail['hasStock'] == 'Y'

    def _insert_histories(self, product_details: [dict]) -> None:
        self.db.insert_site_history([(p['name'], self.fqdn) for p in product_details])

    def _purge_retired_histories(self, product_details: [dict], histories: [tuple]) -> None:
        names = [p['name'] for p in product_details]
        self.db.delete_site_history([h[0] for h in histories if h[1] not in names])

    def _is_not_sent_before(self, product_detail: dict, histories: [tuple]) -> bool:
        name = product_detail['name']
        for h in histories:
            if name == h[1]:
                return False
        return True

    def _generate_text(self, product_detail: dict) -> str:
        name = product_detail['name']
        price = int(product_detail['minPrice'])
        href = f'{self.base_url}/tw/zh_TW/product-detail.html?productCode={product_detail["productCode"]}'
        return f'item: [{name}]({href}) at price: {price}'
