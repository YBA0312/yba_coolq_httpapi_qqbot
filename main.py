#!/usr/bin/env python3
# -*- coding:utf-8 -*-

###############################################################################
# 尽量使用单线程运行，通过协程管理时间片
# 实在无法单线程运行的IO密集型程序，可以调用多线程
# 
# 待解决：
# 判断websocket断开
# 
# 2020/4/26 创建 YBA
###############################################################################

# 网络
import requests
import websockets
# 工具
import os
import sys
import json
import re
import time
# 协程
import asyncio
# 数据库
import pymysql
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
global recv_queue
# 发送队列
global send_queue


def add_message(list, msg):
    data = {}
    data['type'] = 'text'
    data['data'] = {
        'text': msg
    }
    list.append(data)


async def send_message(msg_type, uid, msg_list):
    global send_queue
    priority = post_priority['message'] * 10 + message_priority[msg_type]
    if msg_type == 'private':
        uid_type = 'user_id'
    elif msg_type == 'group':
        uid_type = 'group_id'
    elif msg_type == 'discuss':
        uid_type = 'discuss_id'
    uid_type
    send_msg = {}
    send_msg['action'] = 'send_msg'
    send_msg['params'] = {
        uid_type: uid,
        'message': msg_list
    }
    print(send_msg)
    await send_queue.put((priority, send_msg))


async def process():
    global recv_queue
    while True:
        datas = await recv_queue.get()
        print(datas)
        data = datas[1]
        if data['post_type'] == 'message':
            msg_type = data['message_type']
            if msg_type == 'private':
                uid = data['sender']['user_id']
            elif msg_type == 'group':
                uid = data['group_id']
            elif msg_type == 'discuss':
                uid = data['discuss_id']
            for msg in data['message']:
                print(msg)
                if msg['type'] == 'text':
                    if msg['data']['text'][0] == '/':
                        # IO密集型耗时操作，创建一个新task去处理
                        # asyncio.create_task(example(data))
                        send_msg = []
                        add_message(send_msg, '天天就知道看涩图')
                        await send_message(msg_type, uid, send_msg)


async def ws_recv(websocket):
    global recv_queue
    while True:
        msg = json.loads(await websocket.recv())
        if 'status' in msg:
            print(msg)
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
        await websocket.send(json.dumps(data))


async def ws_client():
    global recv_queue, send_queue
    uri = "ws://localhost:8084/?access_token=0312"
    recv_queue = asyncio.PriorityQueue()
    send_queue = asyncio.PriorityQueue()
    async with websockets.connect(uri) as websocket:

        # 并发写法1，相当于wait()
        # await asyncio.gather(
        #     ws_recv(websocket, recv_queue),
        #     ws_send(websocket, send_queue),
        #     process(recv_queue, send_queue),
        # )
        #
        # 并发写法2，相当于把协程分装成Task
        # 还可以用asyncio.ensure_future和loop.createtask
        Tasks = [
            asyncio.create_task(ws_recv(websocket)),
            asyncio.create_task(ws_send(websocket)),
            asyncio.create_task(process())
        ]
        await asyncio.wait(Tasks)
        # 这里用一个列表写在一起了，也可以：
        #     task1 = asyncio.create_task(task())
        #     await task1
        # 这样来写


if __name__ == '__main__':
    # 练练手，这里使用底层API
    try:
        ws_loop = asyncio.get_event_loop()
        ws_loop.run_until_complete(ws_client())
        ws_loop.run_forever()
    finally:
        ws_loop.run_until_complete(ws_loop.shutdown_asyncgens())
        ws_loop.close()
    # 可以使用高级API，直接写成：
    # asyncio.run(ws_client())


### 闲置函数 ###
'''

def DecodeQR(filename):
    if not os.path.exists(filename):
        raise FileExistsError(filename)

    return pyzbar.decode(Image.open(filename), symbols=[pyzbar.ZBarSymbol.QRCODE])

'''
