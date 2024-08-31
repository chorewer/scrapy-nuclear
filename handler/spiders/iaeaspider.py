import re
from typing import Iterable
import scrapy
from scrapy import Request
from bs4 import BeautifulSoup
from handler.items import pdfItem

class WanospiderSpider(scrapy.Spider):
    name = "iaea"
    allowed_domains = []
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
    base_url = r"https://www.iaea.org"
    def start_requests(self) :
        start_urls = [
            r"https://www.iaea.org/publications/series/all"
        ]

        for link in start_urls:
            yield Request(
                url = link,
                callback=self.parse,
                meta=self.req_meta,
                headers=self.req_headers,
                cb_kwargs=dict()
            )
    def sanitize_filename(self,filename):
        # 定义非法字符的正则表达式
        illegal_chars = r'[<>:"/\\|?*\x00-\x1f]'
        # 移除非法字符
        sanitized = re.sub(illegal_chars, '', filename)
        # 移除以空格或句点结尾的字符
        sanitized = re.sub(r'^\.+|[\. ]+$', '', sanitized)
        # 确保文件名不为空
        if not sanitized:
            raise ValueError("Filename cannot be empty after sanitization")
        return sanitized
    
    def parse(self,response):
        soup = BeautifulSoup(response.text,'html.parser')
        list = soup.find_all('div',class_="pane-publications-type-publication-series-all")
        H4_list = list[0].find_all('h4')
        urls = [(it.find('a').get('href'),it.find('a').get_text()) for it in H4_list]
        self.log(f"there is number {len(urls)} magazines",level=20)
        for link in urls:
            over_path = f'/{self.sanitize_filename(link[1])}'
            yield Request(
                url=self.base_url + link[0],
                cb_kwargs=dict(over_path=over_path,num=0),
                callback=self.second_parse,
                meta=self.req_meta,
                headers=self.req_headers
            )
    
    def second_parse(self,response,over_path,num):
        soup = BeautifulSoup(response.text,'html.parser')
        list = soup.find_all('div',class_="publications-advanced-search")
        if len(list) == 0:
            self.log(f'not found {over_path}',level=20)
            return 
        H4_list = list[1].find_all("h4")
        urls = [
            (
                it.find('a').get('href'),
                self.sanitize_filename(it.find('a').get_text(strip=True))
            ) for it in H4_list
        ]
        self.log(f"the magazine {over_path} have {num+len(H4_list)} books",level=20)
        for href, text in urls:
            yield Request(
                url=self.base_url +href,
                callback=self.download,
                cb_kwargs=dict(over_path=over_path,name=text),
                meta=self.req_meta,
                headers=self.req_headers
            )
        
        resume = soup.find_all("a",title="Go to next page")
        if len(resume)>0:
            self.log(f"the {over_path} have next page for {num + 20}",level=20)
            url = resume[0].get('href')
            yield Request(
                url=self.base_url + url,
                callback=self.second_parse,
                cb_kwargs=dict(over_path=over_path,num=num+len(H4_list)),
                meta=self.req_meta,
                headers=self.req_headers
            )

    def download(self,response,over_path,name):
        soup = BeautifulSoup(response.text, 'html.parser')
        pattern = re.compile(r'\.pdf$')
        url = soup.find_all('a',class_="btn-primary",href=pattern)
        if len(url) > 0:
            self.log(f"the book {name} have a pdf version",level=20)
        for link in url:
            yield Request(
                url = link.get('href'),
                callback=self.load_item,
                cb_kwargs=dict(over_path=over_path,name=name),
                meta=self.req_meta,
                headers=self.req_headers
            )

    def load_item(self,response,over_path,name):
        self.log(f"the book {name} writting to the system",level=20)
        item = pdfItem()
        item['pdf'] = response.body
        item['name'] = name
        item['over_path'] = over_path
        item['type'] = 'pdf'
        return item


    
