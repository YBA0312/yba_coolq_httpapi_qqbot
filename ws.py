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
# 2020/4/29 分离 YBA
###############################################################################

import main
# 网络
import websockets
# 工具
import json
# 协程
import asyncio

class ws():
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


    def __init__(self):
        self.qq = qqbot()

    def add_message(self, list, msg):
        data = {}
        data['type'] = 'text'
        data['data'] = {
            'text': msg
        }
        list.append(data)


    async def send_message(self, msg_type, uid, msg_list):
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


    async def process(self):
        global recv_queue
        while True:
            data = (await recv_queue.get())[1]
            if data['post_type'] == 'message':
                # 获取消息来源类型和uid
                msg_type = data['message_type']
                if msg_type == 'private':
                    uid = data['sender']['user_id']
                elif msg_type == 'group':
                    uid = data['group_id']
                elif msg_type == 'discuss':
                    uid = data['discuss_id']
                # IO密集型耗时操作，创建一个新task去处理
                asyncio.create_task(msg_type, uid, qq.recv_message(data))


    async def ws_recv(self, websocket):
        global recv_queue
        while True:
            msg = json.loads(await websocket.recv())
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


    async def ws_send(self, websocket):
        global send_queue
        while True:
            data = (await send_queue.get())[1]
            await websocket.send(json.dumps(data))


    async def ws_client(self):
        global recv_queue, send_queue
        uri = "ws://localhost:8084/?access_token=0312"
        recv_queue = asyncio.PriorityQueue()
        send_queue = asyncio.PriorityQueue()
        async with websockets.connect(uri) as websocket:

            # 并发写法1，相当于wait()
            # await asyncio.gather(
            #     ws_recv(websocket),
            #     ws_send(websocket),
            #     process(),
            # )
            #
            # 并发写法2，相当于把协程分装成Task
            # 还可以用asyncio.ensure_future和loop.createtask
            Tasks = [
                asyncio.create_task(self.ws_recv(websocket)),
                asyncio.create_task(self.ws_send(websocket)),
                asyncio.create_task(self.process())
            ]
            await asyncio.wait(Tasks)
            # 这里用一个列表写在一起了，也可以：
            #     task1 = asyncio.create_task(task())
            #     await task1
            # 这样来写

'''
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


def DecodeQR(filename):
    if not os.path.exists(filename):
        raise FileExistsError(filename)

    return pyzbar.decode(Image.open(filename), symbols=[pyzbar.ZBarSymbol.QRCODE])

'''
