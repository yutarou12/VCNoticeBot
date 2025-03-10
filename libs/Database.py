import logging
import asyncpg
from functools import wraps

import libs.env as env


class ProductionDatabase:
    def __init__(self):
        self.pool = None

    async def setup(self):
        self.pool = await asyncpg.create_pool(f"postgresql://{env.POSTGRESQL_USER}:{env.POSTGRESQL_PASSWORD}@{env.POSTGRESQL_HOST_NAME}:{env.POSTGRESQL_PORT}/{env.POSTGRESQL_DATABASE_NAME}")

        async with self.pool.acquire() as conn:
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS vc_setting (guild_id bigint NOT NULL PRIMARY KEY, text_ch_id bigint NOT NULL, vc_ch_id bigint NOT NULL)")
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS notice_setting (guild_id bigint NOT NULL PRIMARY KEY, notice_vc BOOLEAN NOT NULL)")

        return self.pool

    def check_connection(func):
        @wraps(func)
        async def inner(self, *args, **kwargs):
            self.pool = self.pool or (await self.setup())
            return await func(self, *args, **kwargs)

        return inner

    @check_connection
    async def execute(self, sql):
        async with self.pool.acquire() as con:
            await con.execute(sql)

    @check_connection
    async def fetch(self, sql):
        async with self.pool.acquire() as con:
            data = await con.fetch(sql)
        return data

    @check_connection
    async def set_vc_setting(self, guild_id: int, text_ch_id: int, vc_ch_id: int):
        await self.execute(f'INSERT INTO vc_setting (guild_id, text_ch_id, vc_ch_id) VALUES ({guild_id}, {text_ch_id}, {vc_ch_id})')

    @check_connection
    async def get_vc_setting(self, guild_id: int):
        data = await self.fetch(f'SELECT * FROM vc_setting WHERE guild_id = {guild_id}')
        if not data:
            return None
        return data[0]

    @check_connection
    async def del_vc_setting(self, guild_id: int):
        async with self.pool.acquire() as con:
            await con.execute('DELETE FROM vc_setting WHERE guild_id = $1', guild_id)

    @check_connection
    async def set_notice_setting(self, guild_id: int, notice_vc: bool):
        await self.execute(f'INSERT INTO notice_setting (guild_id, notice_vc) VALUES ({guild_id}, {notice_vc})')

    @check_connection
    async def get_notice_setting(self, guild_id: int):
        data = await self.fetch(f'SELECT * FROM notice_setting WHERE guild_id = {guild_id}')
        if not data:
            return None
        return data[0]

    @check_connection
    async def del_notice_setting(self, guild_id: int):
        async with self.pool.acquire() as con:
            await con.execute('DELETE FROM notice_setting WHERE guild_id = $1', guild_id)

    @check_connection
    async def update_notice_setting(self, guild_id: int, notice_vc: bool):
        await self.execute(f'UPDATE notice_setting SET notice_vc = {notice_vc} WHERE guild_id = {guild_id}')


class DebugDatabase(ProductionDatabase):
    def __init__(self):
        super().__init__()

    async def execute(self, sql):
        logging.info(f"executing sql: {sql}")

    async def fetch(self, sql):
        logging.info(f"fetching by sql: {sql}")

    async def set_vc_setting(self, guild_id: int, text_ch_id: int, vc_ch_id: int):
        pass


if env.DEBUG is True:
    Database = DebugDatabase
else:
    Database = ProductionDatabase
