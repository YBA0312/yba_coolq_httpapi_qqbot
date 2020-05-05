# //*[@id]/div/a[img]/@href
# //img[@id='image']/@src
from lxml import etree
import asyncio
import uvloop
import aiohttp
import sql
import ujson
import aiofiles
import urllib.parse
import random
import os
import shutil
# http://konachan.net/
# http://konachan.net/post?tags=+-all_male
# https://konachan.net/sample/3a4527460792a52209af3286947d2a0e/Konachan.com%20-%20305816%20sample.jpg

# self.file_list = os.listdir('/home/yba/coolq-data/data/qqbot/konachan')


class konachan():

    def __init__(self):
        self.downloaded_cache_list = []
        self.path = '/home/yba/coolq-data/data/image/'

    async def init(self):
        self.mysql_image = sql.mysql()
        await self.mysql_image.create('qq_image')
        asyncio.create_task(self.image_cache())

    async def get_cache_image(self):
        if len(self.downloaded_cache_list) < 5:
            asyncio.create_task(self.image_cache())
        return self.downloaded_cache_list.pop(0)

    async def image_cache(self):
        rows = await self.mysql_image.fetch('SELECT id FROM `konachan` WHERE `file_name` = NULL')
        urls = await self.get_image_url(random.randint(1, 100), 5)
        print(urls)
        for url in urls:
            asyncio.create_task(self.image_download(url))

    async def image_download(self, url):
        filename = urllib.parse.unquote(os.path.basename(url))
        print(filename)
        async with aiohttp.ClientSession(trust_env=True) as session:
            async with session.get(url) as resp:
                async with aiofiles.open(self.path + filename, mode='wb') as f:
                    await f.write(await resp.read())
        self.downloaded_cache_list.append(filename)
        await self.mysql_image.fetch('UPDATE `konachan` SET `file_name`=\'{}\' WHERE `jpeg_url` = \'{}\''.format(filename, url))
        return filename

    async def get_image_url(self, page=1, limit=1, tags=['-all_male']):
        tags_str = ''
        for tag in tags:
            tags_str = tags_str + '+' + tag
        url = 'http://konachan.net/post.json?page={}&limit={}&tags={}'.format(
            page, limit, tags_str)
        async with aiohttp.ClientSession(trust_env=True) as session:
            async with session.get(url) as resp:
                img_json = ujson.loads(await resp.text())
        img_url = []
        for img in img_json:
            if not await self.mysql_image.fetch('SELECT id FROM `konachan` WHERE img_id = {}'.format(img['id'])):
                await self.mysql_image.fetch('INSERT INTO `konachan`(`img_id`, `tags`, `source`, `file_url`, `preview_url`, `sample_url`, `jpeg_url`, `rating`) VALUES ({},\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\')'
                                             .format(img['id'], ujson.dumps(img['tags'].split(), ensure_ascii=False), img['source'], img['file_url'], img['preview_url'], img['sample_url'], img['jpeg_url'], img['rating']))
                img_url.append(img['jpeg_url'])
        return img_url

# old


class konachan_html():

    def __init__(self):
        self.html_list = set()

    async def get_image_url(self):
        if len(self.html_list) < 15:
            asyncio.create_task(self.add_html())
        url = self.html_list.pop()
        async with aiohttp.ClientSession(trust_env=True) as session:
            async with session.get('http://konachan.net' + url) as resp:
                # print(resp.status)
                # print(await resp.text())
                html = etree.HTML(await resp.text())
                img_url = html.xpath('//img[@id=\'image\']/@src')
                print(img_url)
        return img_url[0]

    async def add_html(self):
        async with aiohttp.ClientSession(trust_env=True) as session:
            async with session.get('http://konachan.net/post?page={}&tags=-all_male'.format(random.randint(1, 100))) as resp:
                # print(resp.status)
                # print(await resp.text())
                html = etree.HTML(await resp.text())
                hlist = html.xpath('//*[@id]/div/a[img]/@href')
                print(hlist)
                self.html_list.update(hlist)
