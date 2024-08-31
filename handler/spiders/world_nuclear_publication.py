import re
from typing import Iterable
import scrapy
from scrapy import Request
from bs4 import BeautifulSoup
from handler.items import pdfItem
from handler.items import MarkDownItem
import html2text

class WorldNuclearSpider(scrapy.Spider):
    name = "worldnuclearpub"
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
            r"https://world-nuclear.org/our-association/publications"
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
        
    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        block = soup.find('div', class_ = 'article_list_manager')
        a_tag = block.find_all('a')
        title = block.find_all('div',class_ = "font_title" )
        self.log(f"found {len(a_tag)} links and matches {len(title)} title",level=20)

        for href, text in zip(a_tag, title):
            # self.log(f"{href.get('href')} + {text.get_text()}" , level=20)
            href = self.base_url + href.get('href')
            text = text.get_text(strip=True)
            yield Request(
                url = href,
                cb_kwargs=dict(over_path = f"/{self.sanitize_filename(text)}"),
                callback=self.second_parse,
                meta=self.req_meta,
                headers=self.req_headers
            )
        
    def second_parse(self,response,over_path):
        soup = BeautifulSoup(response.text, 'html.parser')
        block = soup.find('div', class_='pub_det_body_wrapper')
        head = block.find_all('div',class_="news_box_title")
        a_tag = [it.find('a') for it in head]
        self.log(f'type {over_path} have {len(a_tag)} docs',level=20)
        for it in a_tag:
            href = self.base_url + it.get('href')
            text = it.get_text(strip=True)
            yield Request(
                url=href,
                cb_kwargs=dict(over_path=over_path,title = self.sanitize_filename(text)),
                callback=self.endpoint,
                meta=self.req_meta,
                headers=self.req_headers
            )
    
    def endpoint(self, response, over_path, title):
        soup = BeautifulSoup(response.text, 'html.parser')
        link = soup.find_all('a',href = re.compile(r'\.pdf$'))
        if len(link)>0:
            href_raw = link[0].get('href')
            if  "https" not in href_raw:
                href_raw = self.base_url + href_raw
            yield Request(
                url=href_raw,
                callback=self.download,
                cb_kwargs=dict(over_path=over_path,title=title),
                meta=self.req_meta,
                headers=self.req_headers
            )
        else:
            item = MarkDownItem()
            raw_html = soup.find('main')
            h = html2text.HTML2Text()
            h.ignore_images = True
            h.ignore_links = True
            md_content = h.handle(raw_html.prettify())
            item['name'] = title
            item['type'] = 'md'
            item['md'] = md_content
            item['over_path'] = over_path
            self.log(f'file {title} writing to the system',level=20)
            yield item

    def download(self, response, over_path, title):
        item = pdfItem()
        item['type'] = 'pdf'
        item['pdf'] = response.body
        item['over_path'] = over_path
        item['name'] = title
        self.log(f'file {title} writing to the system',level=20)
        return item


