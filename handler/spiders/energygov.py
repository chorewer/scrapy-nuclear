import re
from typing import Iterable
import scrapy
from scrapy import Request
from bs4 import BeautifulSoup
from handler.items import pdfItem

class WanospiderSpider(scrapy.Spider):
    name = "energygov"
    allowed_domains = []
    req_meta = {
        "max_retry_times": 6,
        "download_timeout": 12
    }

    req_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0',
        'Accept': '*/*',
        'Host': 'www.energy.gov',
        'Connection': 'keep-alive'
    }
    base_url = r"https://www.energy.gov"

    def start_requests(self) :
        start_urls = []
        limit = r"https://www.energy.gov/ne/listings/document-library?page={}"
        for i in range(1,65):
            start_urls.append(f"https://www.energy.gov/ne/listings/document-library?page={i}")

        
        for link, i in zip(start_urls,range(1,65)):
            yield Request(
                url = link,
                callback=self.parse,
                meta=self.req_meta,
                headers=self.req_headers,
                cb_kwargs=dict(page = i)
            )
    
    def parse(self, response,page):
        soup = BeautifulSoup(response.text, 'html.parser')
        h5_list =  soup.find_all('h5')
        num = 0
        for it in h5_list:
            href = it.find('a').get('href')
            text = it.find('a').get_text(strip=True)
            if '.pdf' in href:
                num = num + 1
                yield Request(
                    url = href,
                    callback=self.download,
                    cb_kwargs=dict(name=text),
                    meta=self.req_meta,
                    headers=self.req_headers
                )
        self.log(f'the page {page} load {num} file',level=20)

    def download(self, response, name):
        item = pdfItem()
        item['pdf'] = response.body
        item['name'] = name
        item['type'] = 'pdf'
        item['over_path'] = ""
        return item