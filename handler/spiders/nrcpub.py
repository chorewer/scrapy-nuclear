import re
from typing import Iterable
import scrapy
from scrapy import Request
from bs4 import BeautifulSoup
from handler.items import pdfItem

class NrcSpider(scrapy.Spider):
    name = "nrcpub"
    allowed_domains = []
    req_meta = {
        "max_retry_times": 6,
        "download_timeout": 5
        # "proxy":"http://hk04.allzhen.com:443"
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
        start_link = [
            # r"https://www.nrc.gov/reading-rm/doc-collections/nuregs/staff/index.html",
            r"https://www.nrc.gov/reading-rm/doc-collections/nuregs/brochures/index.html",
            r"https://www.nrc.gov/reading-rm/doc-collections/nuregs/conference/index.html",
            r"https://www.nrc.gov/reading-rm/doc-collections/nuregs/contract/index.html",
            r"https://www.nrc.gov/reading-rm/doc-collections/nuregs/agreement/index.html",
            r"https://www.nrc.gov/reading-rm/doc-collections/nuregs/knowledge/index.html"
        ]
        type = [
            "/staff","/brochures","/conference","/contract","/agreement","/knowledge"
        ]
        for link,mini in zip(start_link,type):
            self.log("SENDING REQUEST",level=200)
            yield Request(
                url=link,
                cb_kwargs=dict(over_path=mini),
                callback=self.parse,
                meta=self.req_meta,
                headers=self.req_headers
            )
    
    def parse(self, response, over_path):
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find('table')
        tr_list = table.find_all('tr')[1:]
        self.log(f"the {over_path} type have a {len(tr_list)} in its table",level=20)
        for it in tr_list:
            td_list = it.find_all('td')
            href = self.base_url + td_list[0].find('a').get('href')
            title = td_list[1].get_text(strip=True)
            title = self.sanitize_filename(title)
            if len(title) > 200:
                title = title[:200]
            yield Request(
                url = href,
                cb_kwargs=dict(over_path=over_path,title=title),
                callback=self.second_parse,
                meta=self.req_meta,
                headers=self.req_headers
            )
        
    def second_parse(self, response, over_path, title):
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if table is not None:
            tr_list = table.find_all('tr')[1:]
            self.log(f"the {title} has a {len(tr_list)} length list let's see more",level=20)
            for it,i in zip(tr_list,range(len(tr_list))):
                td_list = it.find_all('td')
                if td_list[0].find('a') is None:
                    continue
                title_plus = f"version {i}"
                href = td_list[0].find('a').get('href')
                if 'https' not in href:
                    href = self.base_url + href
                yield Request(
                    url = href,
                    cb_kwargs=dict(over_path=over_path,title=title + title_plus),
                    callback=self.download,
                    meta=self.req_meta,
                    headers=self.req_headers
                )
        else:
            self.download(response,over_path,title)
    
    def download(self,response,over_path,title):
        soup = BeautifulSoup(response.text, 'html.parser')
        a_tag = soup.find('a',href=re.compile(r'\.pdf$'))
        href = a_tag.get('href')
        self.log(f"begin writing to file {title}",level=20)
        if 'https' not in href:
            href = self.base_url + href
        yield Request(
            url=href,
            callback=self.make_item,
            cb_kwargs=dict(over_path=over_path,title=title),
            meta=self.req_meta,
            headers=self.req_headers
        )
    
    def make_item(self, response, over_path, title):
        item = pdfItem()
        item['type'] = 'pdf'
        item['pdf'] = response.body
        item['over_path'] = over_path
        item['name'] = title
        return item
