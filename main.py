#!/usr/bin/env python3
# -*- coding:utf-8 -*-

###############################################################################
# 小学生代码，不建议看，浪费时间
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
import random
import bisect
# 协程
import asyncio
import uvloop
# 数据库
import sql
# konachan
import konachan
# 搜图
import saucenao
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

# 信号
signal = {}

my_qq = '1052002233'
super_qq = ['824381616']

###############################################################################


async def recv_message(msg_type, uid, user_id, data):
    global signal
    send_msg = []
    for i in range(len(data['message'])):
        msg = data['message'][i]
        print(msg)
        # @自己
        # 发送缓存图片
        if msg['type'] == 'at' and msg['data'].get('qq') == my_qq:
            # add_message(send_msg, '在呢')
            add_image(send_msg, await k_site.get_cache_image())
        # 收到包含'/涩图 xxx'
        # 查找对应标签图
        elif msg['type'] == 'text':
            if '/涩图' in msg['data'].get('text') or msg['data'].get('text') == '涩图':
                tags = msg['data'].get('text').split()[1:]
                page = 101
                url = []
                if not tags:
                    row = await mysql_hobby.fetch('SELECT `uid` FROM `konachan` WHERE `uid` = \'{}\''.format(user_id))
                    if not row:
                        add_message(send_msg, '请先订阅')
                        continue
                    try:
                        tags = tags + await get_hobby_tag(user_id, 2)
                        tags = tags + await get_hobby_tag(user_id, 2, False)
                    except TypeError:
                        add_message(send_msg, '我还不清楚Master的喜好哦，先标记一些吧')
                        continue
                if msg_type != 'private':
                    tags.append('rating:s')
                while True:
                    url = await k_site.get_image_url(random.randint(1, page), 10, tags)
                    page = int(page / 2)
                    if url or page == 0:
                        break
                if url:
                    filename = await k_site.image_download(url[random.randint(0, len(url)-1)])
                    add_image(send_msg, filename)
                else:
                    add_message(send_msg, '没有找到哦')
                    break
            # /消息回溯 x
            # 查询消息
            elif '/消息回溯' in msg['data'].get('text') and msg_type == 'group':
                m = msg['data'].get('text').split()
                if len(m) > 1:
                    num = m[1]
                    if (num.isdigit()):
                        row = await mysql_chat.fetch('SELECT * FROM `G{}` WHERE `uid` <> \'{}\' ORDER BY id DESC LIMIT {},1'
                                                     .format(uid, my_qq, int(num)-1))
                        if row:
                            add_at(send_msg, row[0][2])
                            add_message(send_msg, '\n{}\n'.format(row[0][1]))
                            send_msg = send_msg + ujson.loads(row[0][3])
                        else:
                            add_message(send_msg, '没有找到哦')
            # 收到管理者包含'/更新标签'
            # 更新tags
            elif '/更新标签' in msg['data'].get('text'):
                if uid in super_qq:
                    add_message(send_msg, '开始更新')
                    await send_message(msg_type, uid, send_msg)
                    send_msg = []
                    # await k_site.update_tags()
                    add_message(send_msg, '更新完成')
                else:
                    add_message(send_msg, '权限不足')
            # /取消订阅
            # 每日推荐
            elif msg['data'].get('text') == '取消订阅' or '/取消订阅' in msg['data'].get('text'):
                if msg_type == 'group':
                    add_message(send_msg, '私戳我')
                elif msg_type == 'private':
                    row = await mysql_hobby.fetch('SELECT * FROM `konachan` WHERE `uid` = \'{}\''.format(user_id))
                    if row:
                        try:
                            await mysql_hobby.fetch('DELETE FROM `konachan` WHERE `uid` = \'{}\''.format(user_id))
                        except:
                            add_message(send_msg, '取消订阅失败')
                            break
                        add_message(send_msg, '取消订阅成功，我将忘记一切关于Master的记忆')
            # /订阅
            # 每日推荐
            elif msg['data'].get('text') == '订阅' or '/订阅' in msg['data'].get('text'):
                if msg_type == 'group':
                    add_message(send_msg, '私戳我')
                elif msg_type == 'private':
                    row = await mysql_hobby.fetch('SELECT * FROM `konachan` WHERE `uid` = \'{}\''.format(user_id))
                    if row:
                        add_message(send_msg, 'Master已经订阅过了')
                    else:
                        try:
                            await mysql_hobby.fetch('INSERT INTO `konachan`(`uid`, `last`) VALUES (\'{}\', \'2000-01-01\')'.format(user_id))
                        except:
                            add_message(send_msg, '订阅失败')
                            break
                        add_message(send_msg, '订阅成功，从今天起你就是我的Master了！\n使用"/涩图"命令将根据你的喜好进行推荐\n')
                        add_message(send_msg, '在任何地方，对于当前聊天的上一张图片，喜欢的扣1，不喜欢的扣2')
            # 1
            # 喜欢推荐
            elif msg['data'].get('text') == '1' or msg['data'].get('text')[0:2] == '1 ':
                row = await mysql_hobby.fetch('SELECT * FROM `konachan` WHERE `uid` = \'{}\''.format(user_id))
                if not row:
                    continue
                if row[0][1]:
                    user_tags = ujson.loads(row[0][1])
                else:
                    user_tags = {}
                user_num = row[0][2]
                num = 1
                m = msg['data'].get('text').split()
                if len(m) > 1:
                    if (m[1].isdigit()):
                        num = int(m[1])
                row = await mysql_chat.fetch('SELECT `msg` FROM `{}{}` WHERE `uid` = \'{}\' AND `msg` LIKE \'%"type": "image"%\' ORDER BY id DESC LIMIT {},1'
                                             .format(msg_type[0].upper(), uid, my_qq, num - 1))
                if row:
                    msg = ujson.loads(row[0][0])
                    filename = msg[0]['data']['file']
                    tags = await k_site.get_tags(filename)
                    for tag in tags:
                        if tag in user_tags:
                            user_tags[tag] = user_tags[tag] + 1
                        else:
                            user_tags[tag] = 1
                    await mysql_hobby.fetch('UPDATE `konachan` SET `tags`=\'{}\',`num` = {} WHERE `uid` = \'{}\''
                                            .format(ujson.dumps(user_tags, ensure_ascii=False).replace("\\", "\\\\").replace("'", "\\'"), user_num + 1, user_id))
                    add_message(send_msg, '(๑•̀ㅂ•́)و✧')
            # 2
            # 不喜欢推荐
            elif msg['data'].get('text') == '2' or msg['data'].get('text')[0:2] == '2 ':
                row = await mysql_hobby.fetch('SELECT * FROM `konachan` WHERE `uid` = \'{}\''.format(user_id))
                if not row:
                    continue
                if row[0][1]:
                    user_tags = ujson.loads(row[0][1])
                else:
                    user_tags = {}
                user_num = row[0][3]
                num = 1
                m = msg['data'].get('text').split()
                if len(m) > 1:
                    if (m[1].isdigit()):
                        num = int(m[1])
                row = await mysql_chat.fetch('SELECT `msg` FROM `{}{}` WHERE `uid` = \'{}\' AND `msg` LIKE \'%"type": "image"%\' ORDER BY id DESC LIMIT {},1'
                                             .format(msg_type[0].upper(), uid, my_qq, num - 1))
                if row:
                    msg = ujson.loads(row[0][0])
                    filename = msg[0]['data']['file']
                    tags = await k_site.get_tags(filename)
                    for tag in tags:
                        if tag in user_tags:
                            user_tags[tag] = user_tags[tag] - 1
                        else:
                            user_tags[tag] = -1
                    await mysql_hobby.fetch('UPDATE `konachan` SET `tags`=\'{}\',`-num` = {} WHERE `uid` = \'{}\''
                                            .format(ujson.dumps(user_tags, ensure_ascii=False).replace("\\", "\\\\").replace("'", "\\'"), user_num + 1, user_id))
                    add_message(send_msg, 'ヽ(ー_ー )ノ')
            elif msg_type == 'private' and msg['data'].get('text'):
                m = msg['data'].get('text').replace("吗","").replace("?","").replace("？","").replace("不","").replace("吗","").replace("我","你")
                add_message(send_msg, m)
    if send_msg:
        await send_message(msg_type, uid, send_msg)


async def get_hobby_tag(uid, c, unsigned=True):
    tags, like_num, unlike_num = (await mysql_hobby.fetch('SELECT `tags`, `num`, `-num` FROM `konachan` WHERE `uid` = \'{}\''.format(uid)))[0]
    if not tags:
        return
    tags = ujson.loads(tags)
    new_tags = {}
    r_tag = []
    if tags:
        if unsigned:
            for tag, value in tags.items():
                if value * 10 > like_num:
                    new_tags[tag] = value
        else:
            for tag, value in tags.items():
                if value * -10 > unlike_num:
                    new_tags['-'+tag] = value * -1
        sorted(new_tags.items(), key=lambda item: item[1], reverse=True)
        for i in range(c):
            if new_tags:
                tags_list = []
                sum_list = []
                sum = 0
                for tag, value in new_tags.items():
                    sum = sum + value
                    sum_list.append(sum)
                    tags_list.append(tag)
                t = random.randint(0, sum - 1)
                t = bisect.bisect_right(sum_list, t)
                del new_tags[tags_list[t]]
                r_tag.append(tags_list.pop(t))
        print(r_tag)
        return r_tag


async def timer():
    pass

###############################################################################


def add_at(list, uid):
    data = {}
    data['type'] = 'at'
    data['data'] = {
        'qq': uid
    }
    list.append(data)


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


async def set_friend_add_request(approve, data):
    global send_queue
    priority = post_priority['request'] * 10 + request_priority['friend']
    send_msg = {}
    send_msg['action'] = 'set_friend_add_request'
    send_msg['params'] = {
        'flag': data['flag'],
        'approve': approve
    }
    print('----------SEND---------')
    print(send_msg)
    await send_queue.put((priority, send_msg))
    send_msg = []
    add_message(send_msg, '添加好友 {}\n{}'.format(
        data['user_id'], data['comment']))
    for uid in super_qq:
        await send_message('private', uid, send_msg)


async def get_version_info():
    send_msg = {'action': 'get_version_info'}
    await send_queue.put((0, send_msg))


async def send_message(msg_type, uid, msg_list):
    global send_queue
    priority = post_priority['message'] * 10 + message_priority[msg_type]
    if msg_type == 'private':
        uid_type = 'user_id'
        table = 'P' + uid
    elif msg_type == 'group':
        uid_type = 'group_id'
        table = 'G' + uid
    elif msg_type == 'discuss':
        uid_type = 'discuss_id'
        table = 'D' + uid
    send_msg = {}
    send_msg['action'] = 'send_msg_async'
    send_msg['params'] = {
        uid_type: uid,
        'message': msg_list
    }
    print('----------SEND---------')
    print(send_msg)
    await send_queue.put((priority, send_msg))
    await mysql_chat.fetch('INSERT INTO `{}` (`datetime`, `uid`, `msg`) VALUES (FROM_UNIXTIME({}), \'{}\', \'{}\')'
                           .format(table, int(time.time()), my_qq, ujson.dumps(send_msg['params']['message'], ensure_ascii=False).replace("\\", "\\\\").replace("'", "\\'")))


async def process():
    global recv_queue
    while True:
        datas = await recv_queue.get()
        # print(datas)
        data = datas[1]
        if data['post_type'] == 'message':
            msg_type = data['message_type']
            if msg_type == 'private':
                uid = str(data['sender']['user_id'])
                user_id = uid
                table = 'P' + uid
            elif msg_type == 'group':
                uid = str(data['group_id'])
                user_id = str(data['sender']['user_id'])
                table = 'G' + uid
            elif msg_type == 'discuss':
                uid = str(data['discuss_id'])
                user_id = str(data['sender']['user_id'])
                table = 'D' + uid
            # IO密集型耗时操作，创建一个新task去处理
            asyncio.create_task(recv_message(msg_type, uid, user_id, data))
            if (not await mysql_chat.fetch('SHOW TABLES LIKE "{}";'.format(table))):
                await mysql_chat.fetch('CREATE TABLE `qq_chat`.`{}` ( `id` INT UNSIGNED NOT NULL AUTO_INCREMENT , `datetime` DATETIME NOT NULL , `uid` VARCHAR(11) NOT NULL , `msg` JSON NOT NULL , PRIMARY KEY (`id`)) ENGINE = InnoDB;'
                                       .format(table))
            await mysql_chat.fetch('INSERT INTO `{}` (`datetime`, `uid`, `msg`) VALUES (FROM_UNIXTIME({}), \'{}\', \'{}\')'
                                   .format(table, data['time'], user_id, ujson.dumps(data['message'], ensure_ascii=False).replace("\\", "\\\\").replace("'", "\\'")))
        elif data['post_type'] == 'request':
            if data['request_type'] == 'friend':
                asyncio.create_task(set_friend_add_request(True, data))


async def ws_recv(websocket):
    global recv_queue
    while True:
        msg = ujson.loads(await websocket.recv())
        print('----------RECV---------')
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
    await mysql_hobby.create('qq_hobby')
    await asyncio.sleep(1)
    await k_site.init()
    await asyncio.sleep(1)
    async with websockets.connect(uri) as websocket:
        # 并发写法1，相当于wait()
        await asyncio.gather(
            ws_recv(websocket),
            ws_send(websocket),
            process(),
            get_version_info(),
            timer()
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
    mysql_hobby = sql.mysql()
    # aiohttp
    k_site = konachan.konachan()
    s_site = saucenao.saucenao()
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
