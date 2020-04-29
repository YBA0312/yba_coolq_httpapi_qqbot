# 数据库
import aiomysql
# 协程
import asyncio
# 工具
import json
import time


class mysql():
    g_pool = None

    def __init__(self):
        pass

    async def fetch(self, data):
        print(data)
        # 从连接池中获取连接
        with (await g_pool) as conn:
            # 用这个连接执行数据库操作
            cursor = await conn.cursor()
            print(cursor)
            await cursor.execute(data)
            rows = await cursor.fetchall()
            print(rows)
            # with 退出后，将自动释放 conn 到 g_pool 中
        return rows

    async def close(self):
        g_pool.close()
        await g_pool.wait_closed()

    async def create(self):
        g_pool = await aiomysql.create_pool(host='localhost',
                                            port=3306,
                                            user='qqbot',
                                            password='0312',
                                            db='qq_chat',
                                            autocommit=True,
                                            minsize=1,
                                            maxsize=30
                                            )
