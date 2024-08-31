# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Item,Field

class HandlerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class pdfItem(Item):
    name = Field()
    over_path = Field() 
    pdf = Field()
    type = Field()

class MarkDownItem(Item):
    name = Field()
    over_path = Field()
    md = Field()
    type = Field()
