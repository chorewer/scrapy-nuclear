import re
from typing import Iterable
import scrapy
from scrapy import Request
from bs4 import BeautifulSoup
from handler.items import pdfItem
from handler.items import MarkDownItem
import html2text

class WorldNuclearSpider(scrapy.Spider):
    name = "worldnuclearinfo"
    req_meta = {
        "max_retry_times": 6,
        "download_timeout": 12
    }

    req_headers = {
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Accept': '*/*',
        # 'Host': 'www.iaea.org',
        'Connection': 'keep-alive'
    }
    base_url = r"https://world-nuclear.org"

    def start_requests(self) :
        start_urls = [
            r"https://world-nuclear.org/information-library/non-power-nuclear-applications",
            r"https://world-nuclear.org/information-library/economic-aspects",
            r"https://world-nuclear.org/information-library/current-and-future-generation",
            r"https://world-nuclear.org/information-library/nuclear-fuel-cycle",
            r"https://world-nuclear.org/information-library/energy-and-the-environment",
            r"https://world-nuclear.org/information-library/safety-and-security",
            r"https://world-nuclear.org/information-library/country-profiles",
            r"https://world-nuclear.org/information-library/facts-and-figures"
        ]
        type = [
            "/non-power-nuclear-applications",
            "/economic-aspects",
            "/current-and-future-generation",
            "/nuclear-fuel-cycle",
            "/energy-and-the-environment",
            "/safety-and-security",
            "/country-profiles",
            "/facts-and-figures"
        ]
        for link,over_path in zip(start_urls,type):
            yield Request(
                url = link,
                callback=self.parse,
                meta=self.req_meta,
                headers=self.req_headers,
                cb_kwargs=dict(over_path = over_path)
            )
    
    def parse(self, response, over_path):
        soup = BeautifulSoup(response.text, 'html.parser')
        block = soup.find('div', class_="pub_det_body_wrapper")
        list = block.find_all('div',class_="news_box_title")
        self.log(f'type in {over_path} have {len(list)} file ',level=20)
        for it in list:
            href = it.find('a').get('href')
            text = it.find('a').get_text()
            yield Request(
                url= self.base_url + href,
                callback= self.download,
                cb_kwargs=dict(over_path=over_path,name=text),
                meta=self.req_meta,
                headers=self.req_headers
            )
    
    def download(self, response, over_path, name):
        soup = BeautifulSoup(response.text, 'html.parser')
        block = soup.find('main')
        h = html2text.HTML2Text()
        h.ignore_images = True
        h.ignore_links = True
        md_content = h.handle(block.prettify())
        item = MarkDownItem()
        item['name'] = name
        item['type'] = 'md'
        item['md'] = md_content
        item['over_path'] = over_path
        self.log(f'file {name} writing to the system',level=20)
        yield item
        pass
    
