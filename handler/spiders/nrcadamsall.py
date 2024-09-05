import re
from typing import Iterable
import scrapy
from scrapy import Request
from bs4 import BeautifulSoup
from scrapy.http import FormRequest
from handler.items import pdfItem
import json
from urllib.parse import urlencode,parse_qs
import logging
class nrcadamsall(scrapy.Spider):
    name = "nrcadamsall"
    allowed_domains = []
    req_meta = {
        "max_retry_times": 6,
        "download_timeout": 120 # 太小了一定会请求不全面
    }

    base_url = r"https://www.nrc.gov"
    
    
    www_headers = {
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Accept': '*/*',
        'Accept-Encoding': "gzip, deflate, br",
        'Content-Type': ' application/x-www-form-urlencoded; charset=UTF-8',
        # 'Host': 'www.nrc.gov',
        'Connection': 'keep-alive'
    }

    folder_body = {
        "limit": '999',# 分页之后每页数量 设为 999 以完全请求每日文档
        "dir": "ASC",# 设置为日期升序
        "sort": "DocumentDate", 
        "initial": "true", # 以下4条均勿动
        "fieldSet": "pars",
        "formatSet": "default",
        "treeLevel": "1|1",
        "start": '0',
        "filters": '{"operation": "and","operand": []}',
        "nodeContext": '{"FolderPath":"/Recent Released Documents/August 2024/August 29, 2024"}', # 唯一的需要改变的地方 即 年份月份和日期
        "treeModel": '{"name":"CEFoldersWithRoot","properties":[{"id":"FolderPath","value":"/Recent Released Documents"},{"id":"DataProviderId","value":"ce_bp8os_repository"}]}' 
        # treeModel 勿动
    }
    children_body = {
        "start": '0',
        "limit": '20',
        "dir": "ASC",
        "fieldSet": "compound",
        "tabId": "folder-view-tab",
        "ids": "",
        "filters": '{"operation": "and","operand": []}'
    }
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
    
    def abbreviate_title(self, title):
        abbreviations = {
            "for": "4",
            "to": "2",
            "and": "&",
            "with": "w-",
            "the": "th"
        }
        for word, abbr in abbreviations.items():
            title = title.replace(word, abbr)
        return title
    def smart_truncate_title(self, title, max_length):
        if len(title) <= max_length:
            return title
        truncated_title = title[:max_length]
        last_space = truncated_title.rfind(' ')
        if last_space != -1:
            truncated_title = truncated_title[:last_space]
        return truncated_title
    def start_requests(self) :
        url = "https://adams.nrc.gov/wba/services/tree/getFolderDocs"

        folder_data = '{"FolderPath":"/Recent Released Documents/August 2024/August 29, 2024"}'
        month = ["January","February","March","April","May","June","July","August"]#,"September","October","November","December"]
        for it in month:
            for i in range(1,31):
                folder_data = '{"FolderPath":"/Recent Released Documents/'+it+' 2024/'+it+' '+str(i).zfill(2)+', 2024"}'
                form_data = self.folder_body
                form_data["nodeContext"] = folder_data
                over_path = f"/{it} 2024/{it} {i}"
                # encoded_body = urlencode(form_data)
                req =  FormRequest(
                    url = url,
                    formdata=form_data,
                    method="POST",
                    callback=self.parse,
                    cb_kwargs=dict(over_path = over_path),
                    meta=self.req_meta,
                    headers=self.www_headers
                )
                yield req
        
    def parse(self, response, over_path):
        
        json_data = response.json()
        # self.log(str(json_data),level=20)
        links_list = []
        viewurl = f"https://adamswebsearch2.nrc.gov/webSearch2/view"
        childrenurl = f"https://adams.nrc.gov/wba/services/properties/children"
        self.log(f"there is {len(json_data["docs"])} in the day {over_path}",level=20)
        for it in json_data["docs"]:
            number = it["properties"]["AccessionNumber"]
            title = it["title"]
            compound = it["documentId"]["compound"]
            if compound == False:
                data_form = {
                    "AccessionNumber": number
                }
                encoded_body = urlencode(data_form)
                
                yield Request(
                    url=viewurl,
                    method="POST",
                    body=encoded_body,
                    callback=self.download,
                    cb_kwargs=dict(over_path = over_path, title = title),
                    meta=self.req_meta,
                    headers=self.www_headers
                )
            elif compound == True:
                children_body = self.children_body
                children_body["ids"] = it["documentId"]
                encoded_body = urlencode(children_body)
                yield Request(
                    url = childrenurl,
                    callback=self.secondparse,
                    method="POST",
                    body=encoded_body,
                    cb_kwargs=dict(over_path=over_path, title=title),
                    meta=self.req_meta,
                    headers=self.www_headers
                )
    def fix_json(self, json_str):
        # 正则表达式匹配未加引号的键名
        pattern = re.compile(r'(\b[a-zA-Z_][a-zA-Z0-9_]*\b):')
        
        # 使用正则表达式替换未加引号的键名为加引号的键名
        fixed_json_str = pattern.sub(r'"\1":', json_str)
        
        return fixed_json_str
        
    def secondparse(self, response, over_path, title):
        json_data = None
        try:
            json_data = response.json()
        except json.JSONDecodeError as e:
            try:
                json_data = json.loads(self.fix_json(response.text))
            except json.JSONDecodeError as e:
                self.log(f"Error decoding JSON: {e} Raw response content:{response.text}",logging.ERROR)
                return
        index = 0
        viewurl = f"https://adamswebsearch2.nrc.gov/webSearch2/view"
        self.log(f"deeper parse the title {title}, have {len(json_data["docs"])} in it",level=20)
        for it in json_data["docs"]:
            number = it["properties"]["AccessionNumber"]
            title = title + "vol. " + str(index)
            
            data_form = {
                "AccessionNumber": number
            }
            encoded_body = urlencode(data_form)
            index = index + 1
            yield Request(
                url=viewurl,
                method="POST",
                headers=self.www_headers,
                meta=self.req_meta,
                callback=self.download,
                body=encoded_body,
                cb_kwargs=dict(over_path=over_path,title = title)
            )
    
    def download(self, response, over_path, title):
        item = pdfItem()
        item['type'] = 'pdf'
        item['pdf'] = response.body
        item['over_path'] = over_path
        title = self.abbreviate_title(title)
        title = self.smart_truncate_title(title, 130)
        title = self.sanitize_filename(title)
        item['name'] = title
        return item
            
           
