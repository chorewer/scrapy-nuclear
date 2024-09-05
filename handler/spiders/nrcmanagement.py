import re
from typing import Iterable
import scrapy
from scrapy import Request
from bs4 import BeautifulSoup
from handler.items import pdfItem

class NrcSpider(scrapy.Spider):
    name = "nrcmanagedevice"
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
        for i in range(1,15):
            url_t = f"https://www.nrc.gov/reading-rm/doc-collections/management-directives/volumes/vol-{i}.html"
            start_link.append(url_t)
        self.log(f"there are {len(start_link)} volume file need to crawl ",level=200)
        for link, mini in zip(start_link,range(1,15)):
            mini = f'/volume-{mini}'
            yield Request(
                url=link,
                cb_kwargs=dict(over_path=mini,vol=mini),
                callback=self.parse,
                meta=self.req_meta,
                headers=self.req_headers
            )
    
    def parse(self, response, over_path, vol):
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        tr_list = table.find_all('tr')[1:]
        req_list = []
        for it in tr_list:
            td_list = it.find_all('td')
            a_tag = td_list[0].find('a',href=re.compile(r'\.pdf$'))
            title = td_list[1].get_text()
            if a_tag is None:
                continue
            href = a_tag.get('href')
            req_list.append((title, href))
        self.log(f'the volume {vol} have {len(req_list)} file , crawling ... ',level=20)
        for title, href in req_list:
            title = self.sanitize_filename(title)
            yield Request(
                url = self.base_url + href,
                callback = self.download,
                cb_kwargs = dict(over_path=over_path,title=title),
                meta = self.req_meta,
                headers = self.req_headers
            )
    
    def download(self, response, over_path, title):
        item = pdfItem()
        item['type'] = 'pdf'
        item['pdf'] = response.body
        item['over_path'] = over_path
        item['name'] = title
        return item
