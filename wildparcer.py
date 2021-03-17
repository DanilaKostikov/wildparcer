import requests
import bs4
import logging
import collections
import csv
import sys
import time
import random
import re
import gc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('wb')

sys.setrecursionlimit(10**6)

ParseResult = collections.namedtuple(
    'ParseResult',
    (
        'brand_name',
        'goods_name',
        'url',
        'article',
        'price',
        'popularity',
        'rating',
    ),
)

HEADERS = (
    'Бренд',
    'Товар',
    'Ссылка',
    'Артикул',
    'Цена',
    'Популярность',
    'Оценка',
)

NUMBER_FILE = 1

class Client:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'ozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
            'Accept-Language': 'ru',
        }
        self.result = []
        self.number_of_products = 0

    def load_global_section(self, text: str):
        url = text
        res = self.session.get(url=url)
        res.raise_for_status()
        res = res.text
        soup = bs4.BeautifulSoup(res, 'lxml')
        container = soup.select_one('ul.maincatalog-list-2')
        container = container.select('li')

        for block in container:
            block = block.select_one('a')
            url = block.get('href')
            url_addition = 'https://www.wildberries.ru'
            url = url_addition + url
            logger.info(url)
            self.load_section(text=url)

    def load_section(self, text: str):
        #time.sleep(random.randrange(0, 200, 1)/100)
        url_n = text
        res = self.session.get(url=url_n)
        res.raise_for_status()
        res = res.text
        soup = bs4.BeautifulSoup(res, 'lxml')
        container = soup.select_one('a.pagination-next')
        text_2 = self.load_page(url_n)
        self.pars_page(text=text_2)
        self.save_result()
        self.result = []
        logger.debug(url_n)
        if container:
            url = container.get('href')
            url_addition = 'https://www.wildberries.ru'
            url = url_addition + url
            soup = None
            container = None
            text_2 = None
            res = None
            gc.collect()
            return self.load_section(text=url)
        return

    def load_page(self, text: str):
        url = text
        res = self.session.get(url=url)
        res.raise_for_status()
        logger.info(url)
        return res.text

    def pars_page(self, text: str):
        soup = bs4.BeautifulSoup(text, 'lxml')
        container = soup.select('div.dtList.i-dtList.j-card-item')
        for block in container:
            self.pars_block(block=block)
        container = None
        gc.collect()

    def pars_block(self, block):
        url_block = block.select_one('a.ref_goods_n_p')
        if not url_block:
            logger.error('no url_block')
            return

        url = url_block.get('href')
        if not url:
            logger.error('no url')
            return

        logger.debug('%s', url)

        name_block = block.select_one('div.dtlist-inner-brand-name')
        if not name_block:
            logger.error(f'no name_block on {url}')
            return

        brand_name = name_block.select_one('strong.brand-name')
        if not brand_name:
            logger.error(f'no brand_name on {url}')
            return

        brand_name = brand_name.text
        brand_name = brand_name.replace('/', '').strip()

        logger.debug('%s', brand_name)

        goods_name = name_block.select_one('span.goods-name')
        if not goods_name:
            logger.error(f'no goods_name on {url}')
            return

        goods_name = goods_name.text.strip()

        logger.debug('%s', goods_name)

        container = block
        if container:
            contatiner = container.get('data-popup-nm-id')
            articul = contatiner
        else:
            articul = 'Артикула нет'

        logger.debug(articul)

        container = block.select_one('ins.lower-price')
        if container:
            price = container.text.strip()
            price = re.sub("[^0-9]", "", price)
            price = int(price)
        else:
            container = block.select_one('span.lower-price')
            if container:
                price = container.text.strip()
                price = re.sub("[^0-9]", "", price)
                price = int(price)
            else:
                price = 'Цены нет'

        logger.debug(price)

        container = block.select_one('span.dtList-comments-count.c-text-sm')
        if container:
            popularity = container.text.strip()
            popularity = re.sub("[^0-9]", "", popularity)
            popularity = int(popularity)
        else:
            popularity = 'Отзывов нет'

        logger.debug(popularity)

        container = block.select_one('span.c-stars-line-lg.j-stars.stars-line-sm')
        if container:
            rating = container.get('class')
            try:
                rating = rating[3]
                rating = rating[4]
                rating = int(rating)
                rating = rating/5*10
            except Exception:
                rating = 'Нет отзывов.'
        else:
            rating = 'Нет отзывов.'

        if popularity == 0:
            rating = 'Нет отзывов.'

        logger.debug(rating)

        self.result.append(ParseResult(
            url=url,
            brand_name=brand_name,
            goods_name=goods_name,
            article=articul,
            price=price,
            popularity=popularity,
            rating=rating,
        ))
        url_block = None
        url = None
        brand_name = None
        goods_name = None
        articul = None
        price = None
        popularity = None
        rating = None
        container = None
        gc.collect()
        logger.debug('-' * 100)

    def save_result(self):
        global NUMBER_FILE, HEADERS
        if self.number_of_products >= 200000:
            NUMBER_FILE += 1
            self.number_of_products = 0
            path = 'C:/Users/DanKos/PycharmProjects/wildparcer/wild' + str(NUMBER_FILE) + '.csv'
            f = open(path, "x")
            f.close()
            with open(path, 'w', encoding='utf8') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
                for item in self.result:
                    writer.writerow(HEADERS)
                    writer.writerow(item)
                    self.number_of_products += 1
            f = None
            gc.collect()
        else:
            path = 'C:/Users/DanKos/PycharmProjects/wildparcer/wild' + str(NUMBER_FILE) + '.csv'
            with open(path, 'a', encoding='utf8') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
                for item in self.result:
                    writer.writerow(item)
                    self.number_of_products += 1
                logger.info(f'Товаров сохранено {self.number_of_products}')
            f = None
            gc.collect()

    def run(self, text: str):
        self.load_global_section(text=text)


if __name__ == '__main__':
    parser = Client()
    parser.run('https://www.wildberries.ru/catalog/zhenshchinam')
    parser.run('https://www.wildberries.ru/catalog/muzhchinam')
    parser.run('https://www.wildberries.ru/catalog/detyam')
    parser.run('https://www.wildberries.ru/catalog/obuv')
    parser.run('https://www.wildberries.ru/catalog/aksessuary')
    parser.run('https://www.wildberries.ru/catalog/elektronika')
    parser.run('https://www.wildberries.ru/catalog/bytovaya-tehnika')
    parser.run('https://www.wildberries.ru/catalog/knigi')
    parser.load_section('https://www.wildberries.ru/catalog/sport/vidy-sporta/fitnes/yoga')
    parser.run('https://www.wildberries.ru/catalog/krasota')
    parser.run('https://www.wildberries.ru/catalog/igrushki')
    parser.run('https://www.wildberries.ru/catalog/pitanie')
    parser.run('https://www.wildberries.ru/catalog/tovary-dlya-zhivotnyh')
    parser.run('https://www.wildberries.ru/catalog/knigi-i-diski/kantstovary')
    parser.run('https://www.wildberries.ru/catalog/dom-i-dacha/zdorove')
    parser.run('https://www.wildberries.ru/catalog/dom-i-dacha/instrumenty')
    parser.run('https://www.wildberries.ru/catalog/dom-i-dacha')
    parser.run('https://www.wildberries.ru/catalog/aksessuary/avtotovary')
    parser.run('https://www.wildberries.ru/catalog/yuvelirnye-ukrasheniya')