# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pathlib import Path
from scrapy.spiders import Spider
from scrapy import Item
import logging

class HandlerPipeline:
    def process_item(self, item, spider):
        return item

class PdfPipeline:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        Path(self.base_dir).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            base_dir = crawler.settings.get("BASE_DIR")
        )

    def download_pdf(self, file, output_path):
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(file)
        logging.warning(f"successfully write the {output_path}")
        

    def process_item(self, item:Item, spider:Spider):
        # 在每一次得到数据时候被调用
        if item.get("type")!="pdf" : 
            return item
        
        spider_path = f"/{spider.name}"
        over_path = item.get("over_path")
        pdf_path = f"/{item.get("name")}"
        binary = item.get("pdf")
        
        file_path = f"{self.base_dir}{spider_path}{over_path}{pdf_path}.pdf"
        self.download_pdf(binary,file_path)

        return item


class MarkDownPipeline:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        Path(self.base_dir).mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            base_dir = crawler.settings.get("BASE_DIR")
        )
    
    def download_md(self, file, output_path):
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(file,encoding='utf-8')
        logging.warning(f"successfully write the {output_path}")

    def process_item(self, item:Item, spider:Spider):
        # 在每一次得到数据时候被调用
        if item.get("type")!="md" : 
            return item
        
        spider_path = f"/{spider.name}"
        over_path = item.get("over_path")
        pdf_path = f"/{item.get("name")}"
        text = item.get("md")
        
        file_path = f"{self.base_dir}{spider_path}{over_path}{pdf_path}.md"
        self.download_md(text,file_path)

        return item