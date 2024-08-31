import re
from typing import Iterable
import scrapy
from scrapy import Request
from bs4 import BeautifulSoup
from handler.items import pdfItem

class NrcSpider(scrapy.Spider):
    name = "nrcresearch"
    allowed_domains = []
    req_meta = {
        "max_retry_times": 6,
        "download_timeout": 60
    }

    req_headers = {
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Accept': '*/*',
        'Host': 'www.nrc.gov',
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
        num = []
        for i in range(1974,2025):
            start_link.append(
                f"https://www.nrc.gov/reading-rm/doc-collections/research-info-letters/{i}/index.html"
            )
            num.append(i)
        for it,i in zip(start_link,num):
            over_path = f"/{i}"
            yield Request(
                url=it,
                callback=self.parse,
                cb_kwargs=dict(over_path = over_path),
                meta=self.req_meta,
                headers=self.req_headers
            )
    
    def parse(self, response, over_path):
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        col = table.find_all('tr')
        if len(col) < 2:
            return
        col = col[1:]
        self.log(f"year {over_path} have {len(col)} file",level=20)
        for it in col:
            td = it.find_all('td')
            if len(td) < 1:
                continue
            href = td[-1].find('a')
            if href is None:
                continue
            href = href.get('href')
            href = self.base_url + href
            text = td[-2].get_text()
            text = self.sanitize_filename(text)
            yield Request(
                url = href,
                callback=self.download,
                cb_kwargs=dict(over_path=over_path,name = text),
                meta=self.req_meta,
                headers=self.req_headers
            )
    
    def download(self, response, over_path, name):
        item = pdfItem()
        item['type'] = 'pdf'
        item['pdf'] = response.body
        item['name'] = name 
        item["over_path"] = over_path
        return item