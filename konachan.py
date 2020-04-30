# //*[@id]/div/a[img]/@href
# //img[@id='image']/@src
from lxml import etree
import asyncio
import aiohttp
import aiofiles
import random
import os
import shutil
# http://konachan.net/
# http://konachan.net/post?tags=+-all_male
# https://konachan.net/sample/3a4527460792a52209af3286947d2a0e/Konachan.com%20-%20305816%20sample.jpg


class konachan():

    def __init__(self):
        self.html_list = set()
        self.file_list = os.listdir('/home/yba/coolq-data/data/qqbot/konachan')
        self.file_list.remove('old')

    async def get_image_url(self):
        if len(self.html_list) < 15:
            asyncio.create_task(self.add_html())
        url = self.html_list.pop()
        async with aiohttp.ClientSession() as session:
            async with session.get('http://konachan.net' + url) as resp:
                # print(resp.status)
                # print(await resp.text())
                html = etree.HTML(await resp.text())
                img_url = html.xpath('//img[@id=\'image\']/@src')
                print(img_url)
        return img_url[0]



    async def add_html(self):
        async with aiohttp.ClientSession() as session:
            async with session.get('http://konachan.net/post?page={}&tags=-all_male'.format(random.randint(1,100))) as resp:
                # print(resp.status)
                # print(await resp.text())
                html = etree.HTML(await resp.text())
                hlist = html.xpath('//*[@id]/div/a[img]/@href')
                print(hlist)
                self.html_list.update(hlist)

