import asyncio
# 二维码
import qrcode
import pyzbar
# 其他文件
import ws
import sql


class qqbot():
    mysql_qq_chat = None

    async def __init__(self):
        pass
        # mysql_qq_chat = sql.mysql()
        # await mysql_qq_chat.create()

    async def recv_message(self, msg_type, uid, data):
        # 写入数据库
        # print(await mysql_qq_chat.fetch('select version();'))
        # 处理消息
        for msg in data['message']:
            print(msg)
            if msg['type'] == 'text':
                if msg['data']['text'][0] == '/':
                    send_msg = []
                    ws.add_message(send_msg, '天天就知道看涩图')
                    await ws.send_message(msg_type, uid, send_msg)


if __name__ == '__main__':
    ws = ws()
    asyncio.run(ws.ws_client())
