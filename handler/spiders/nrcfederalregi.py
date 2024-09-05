import re
from typing import Iterable
import scrapy
from scrapy import Request
from bs4 import BeautifulSoup
from handler.items import pdfItem

class NrcSpider(scrapy.Spider):
    name = "nrcregistry"
    allowed_domains = []
    req_meta = {
        "max_retry_times": 6,
        "download_timeout": 5
        # "proxy":"http://hk04.allzhen.com:443"
    }
    req_headers = {
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Accept': '*/*',
        # 'Host': 'www.nrc.gov',
        'Connection': 'keep-alive'
    }
    base_url = r"https://www.nrc.gov"

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

    def start_requests(self) :
        start_link = []
        for i in range(2003,2025):
            url_t = f"https://www.nrc.gov/reading-rm/doc-collections/fedreg/notices/{i}.html"
            start_link.append(url_t)
        self.log(f"there are {len(start_link)} year file need to crawl ",level=200)
        for link, mini in zip(start_link,range(2003,2025)):
            mini = f'/{mini}'
            yield Request(
                url=link,
                cb_kwargs=dict(over_path=mini,year=mini),
                callback=self.parse,
                meta=self.req_meta,
                headers=self.req_headers
            )
        
    def parse(self, response, over_path,year):
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        tr_list = table.find_all('tr')
        req_list = []
        for it in tr_list:
            td_list = it.find_all("td")
            if len(td_list) > 1:
                title =td_list[0].get_text()
                a_tag = td_list[1].find('a',href=re.compile(r'\.pdf$'))
                if a_tag is None: 
                    continue
                href = a_tag.get('href')
                req_list.append((title, href))
        self.log(f"the year {year} have {len(req_list)} file to crawl , doing ... ",level= 200)
        for title, href in req_list:
            yield Request(
                url = href,
                callback=self.download,
                cb_kwargs=dict(over_path=over_path,name=title),
                meta=self.req_meta,
                headers=self.req_headers
            )
    
    def download(self, response, over_path, name):
        item = pdfItem()
        item['type'] = 'pdf'
        item['pdf'] = response.body
        item['over_path'] = over_path
        item['name'] = name
        return item
