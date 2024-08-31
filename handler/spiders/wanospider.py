import scrapy
from scrapy import Request
from bs4 import BeautifulSoup
from handler.items import pdfItem

class WanospiderSpider(scrapy.Spider):
    name = "wano"
    allowed_domains = ["www.wano.info"]
    
    req_meta = {
        "max_retry_times": 6,
        "download_timeout": 12
    }

    req_headers = {
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Accept': '*/*',
        'Host': 'www.wano.info',
        'Connection': 'keep-alive'
    }

    def start_requests(self):
        start_urls = [
            "https://www.wano.info/resources/",
            "https://www.wano.info/resources/?sf_paged=2",
            "https://www.wano.info/resources/?sf_paged=3",
            "https://www.wano.info/resources/?sf_paged=4"
        ]

        for link in start_urls:
            yield Request(
                url=link,
                callback = self.HTMLparse,
                headers = self.req_headers,
                meta = self.req_meta,
                cb_kwargs=dict(),
            )
    
    def HTMLparse(self,response):
        soup = BeautifulSoup(response.text, 'html.parser')
        panel = soup.find_all("div", class_="search-filter-results")
        H3_tag = panel[0].find_all("h3")
        pairs = [
            (
                it.find_all('a')[0].get('href'),
                it.find_all('a')[0].get_text(strip=True)
            ) for it in H3_tag
            if len(it.find_all('a')) > 0
        ]
        for it in pairs:
            self.log(it[0],level=20)
            yield Request(
                url=it[0],
                callback=self.pdfparse,
                cb_kwargs=dict(title=it[1]),
                meta=self.req_meta,
                headers=self.req_headers
            )
    
    def pdfparse(self,response,title):
        item = pdfItem()
        item['name'] = title
        item['over_path'] = ""
        item['type'] = 'pdf'
        item['pdf'] = response.body
        return item
