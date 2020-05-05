#!/usr/bin/env python3
# -*- coding:utf-8 -*-

###############################################################################
# 备忘录
# 
# 待解决：
# 判断websocket断开
###############################################################################

# 网络
# import requests
import websockets
# 工具
# import os
# import shutil
# import sys
import ujson
import re
import time
# 协程
import asyncio
import uvloop
# 数据库
import sql
# konachan
import konachan
# 二维码
# import qrcode
# import pyzbar

# 回调类型优先级
post_priority = {'message': 1, 'notice': 2, 'request': 3, 'meta_event': 4}
# 消息来源优先级
message_priority = {'private': 1, 'group': 2, 'discuss': 3}
# 请求优先级
request_priority = {'friend': 1, 'group': 2}
# 事件优先级
notice_priority = {'friend_add': 1, 'group_ban': 3, 'group_increase': 3,
                   'group_decrease': 3, 'group_admin': 3, 'group_upload': 2}
# 元事件优先级
meta_event_priority = {'lifecycle': 1, 'heartbeat': 1}

# 接收队列
recv_queue = None
# 发送队列
send_queue = None

my_qq = '1052002233'
super_qq = ['824381616']

###############################################################################

async def recv_message(msg_type, uid, data):
    send_msg = []
    for msg in data['message']:
        print(msg)
        if msg['type'] == 'at' and msg['data'].get('qq') == my_qq:
            add_message(send_msg, '在呢')
            await k_site.image_cacha()
        elif msg['type'] == 'text' and '图' in msg['data'].get('text'):
            print('in')
            add_image(send_msg, await k_site.get_cache_image())
    if send_msg:
        await send_message(msg_type, uid, send_msg)


###############################################################################

def add_image(list, img):
    data = {}
    data['type'] = 'image'
    data['data'] = {
        'file': img
    }
    list.append(data)


def add_message(list, msg):
    data = {}
    data['type'] = 'text'
    data['data'] = {
        'text': msg
    }
    list.append(data)


async def get_version_info():
    send_msg = {'action':'get_version_info'}
    await send_queue.put((0, send_msg))


async def send_message(msg_type, uid, msg_list):
    global send_queue
    priority = post_priority['message'] * 10 + message_priority[msg_type]
    if msg_type == 'private':
        uid_type = 'user_id'
        table = 'P' + str(uid)
    elif msg_type == 'group':
        uid_type = 'group_id'
        table = 'G' + str(uid)
    elif msg_type == 'discuss':
        uid_type = 'discuss_id'
        table = 'D' + str(uid)
    send_msg = {}
    send_msg['action'] = 'send_msg_async'
    send_msg['params'] = {
        uid_type: uid,
        'message': msg_list
    }
    print(send_msg)
    await send_queue.put((priority, send_msg))
    await mysql_chat.fetch('INSERT INTO `{}` (`datetime`, `uid`, `msg`) VALUES (FROM_UNIXTIME({}), \'{}\', \'{}\')'.format(table, int(time.time()), my_qq, ujson.dumps(send_msg['params']['message'], ensure_ascii=False)))


async def process():
    global recv_queue
    while True:
        datas = await recv_queue.get()
        # print(datas)
        data = datas[1]
        if data['post_type'] == 'message':
            msg_type = data['message_type']
            if msg_type == 'private':
                uid = data['sender']['user_id']
                user_id = uid
                table = 'P' + str(uid)
            elif msg_type == 'group':
                uid = data['group_id']
                user_id = data['sender']['user_id']
                table = 'G' + str(uid)
            elif msg_type == 'discuss':
                uid = data['discuss_id']
                user_id = data['sender']['user_id']
                table = 'D' + str(uid)
            # IO密集型耗时操作，创建一个新task去处理
            asyncio.create_task(recv_message(msg_type, uid, data))
            if (not await mysql_chat.fetch('SHOW TABLES LIKE "{}";'.format(table))):
                await mysql_chat.fetch('CREATE TABLE `qq_chat`.`{}` ( `id` INT UNSIGNED NOT NULL AUTO_INCREMENT , `datetime` DATETIME NOT NULL , `uid` VARCHAR(11) NOT NULL , `msg` JSON NOT NULL , PRIMARY KEY (`id`)) ENGINE = InnoDB;'.format(table))
            await mysql_chat.fetch('INSERT INTO `{}` (`datetime`, `uid`, `msg`) VALUES (FROM_UNIXTIME({}), \'{}\', \'{}\')'.format(table, data['time'], user_id, ujson.dumps(data['message'], ensure_ascii=False).replace("\\", "\\\\")))


async def ws_recv(websocket):
    global recv_queue
    while True:
        msg = ujson.loads(await websocket.recv())
        print(msg)
        if 'status' in msg:
            continue
        if msg['post_type'] == 'message':
            priority = post_priority['message']*10 + \
                message_priority[msg['message_type']]
        elif msg['post_type'] == 'notice':
            priority = post_priority['notice']*10 + \
                notice_priority[msg['notice_type']]
        elif msg['post_type'] == 'request':
            priority = post_priority['request']*10 + \
                request_priority[msg['request_type']]
        elif msg['post_type'] == 'meta_event':
            priority = post_priority['meta_event']*10 + \
                meta_event_priority[msg['meta_event_type']]
        await recv_queue.put((priority, msg))


async def ws_send(websocket):
    global send_queue
    while True:
        data = (await send_queue.get())[1]
        await websocket.send(ujson.dumps(data))


async def ws_client():
    global recv_queue, send_queue, mysql_chat
    uri = "ws://localhost:8084/?access_token=0312"
    recv_queue = asyncio.PriorityQueue()
    send_queue = asyncio.PriorityQueue()
    await mysql_chat.create('qq_chat')
    await k_site.init()
    async with websockets.connect(uri) as websocket:
        # 并发写法1，相当于wait()
        await asyncio.gather(
            ws_recv(websocket),
            ws_send(websocket),
            process(),
            get_version_info()
        )
        #
        # 并发写法2，相当于把协程分装成Task
        # 还可以用asyncio.ensure_future和loop.createtask
        # Tasks = [
        #     asyncio.create_task(ws_recv(websocket)),
        #     asyncio.create_task(ws_send(websocket)),
        #     asyncio.create_task(process())
        # ]
        # await asyncio.wait(Tasks)
        # 这里用一个列表写在一起了，也可以：
        #     task1 = asyncio.create_task(task())
        #     await task1
        # 这样来写


if __name__ == '__main__':
    # 创建MySQL连接池
    mysql_chat = sql.mysql()
    # aiohttp
    k_site = konachan.konachan()
    # 练练手，这里使用底层API
    # try:
    #     ws_loop = asyncio.get_event_loop_policy()
    #     ws_loop.run_until_complete(ws_client())
    #     ws_loop.run_forever()
    # finally:
    #     ws_loop.run_until_complete(ws_loop.shutdown_asyncgens())
    #     ws_loop.close()
    # 可以使用高级API，直接写成：
    uvloop.install()
    asyncio.run(ws_client())


### 闲置函数 ###
'''

def DecodeQR(filename):
    if not os.path.exists(filename):
        raise FileExistsError(filename)

    return pyzbar.decode(Image.open(filename), symbols=[pyzbar.ZBarSymbol.QRCODE])

'''
