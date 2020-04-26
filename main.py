#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# 网络
import requests
import websockets
# 工具
import os
import sys
import json
import time
# 协程
import asyncio
# 二维码
import qrcode
import pyzbar

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


async def process(recv_queue, send_queue):
    while True:
        data = await recv_queue.get()
        print(data)
        # await asyncio.sleep(10)


async def ws_recv(websocket, recv_queue):
    while True:
        msg = json.loads(await websocket.recv())
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


async def ws_send(websocket, send_queue):
    while True:
        data = await send_queue.get()
        # await asyncio.sleep(10)


async def ws_client():
    uri = "ws://localhost:8084/?access_token=0312"
    # 接收队列
    recv_queue = asyncio.PriorityQueue()
    # 发送队列
    send_queue = asyncio.PriorityQueue()
    async with websockets.connect(uri) as websocket:
        # 并发
        await asyncio.gather(
            ws_recv(websocket, recv_queue),
            ws_send(websocket, send_queue),
            process(recv_queue, send_queue),
        )


if __name__ == '__main__':
    # 练练手，这里使用低级API单独处理websocket
    try:
        ws_loop = asyncio.new_event_loop()
        ws_loop.run_until_complete(ws_client())
        ws_loop.run_forever()
    finally:
        ws_loop.run_until_complete(ws_loop.shutdown_asyncgens())
        ws_loop.close()


### 闲置函数 ###


def DecodeQR(filename):
    if not os.path.exists(filename):
        raise FileExistsError(filename)

    return pyzbar.decode(Image.open(filename), symbols=[pyzbar.ZBarSymbol.QRCODE])
