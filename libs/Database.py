import os
import hashlib
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
                "CREATE TABLE IF NOT EXISTS notice_setting (guild_id bigint NOT NULL PRIMARY KEY, notice_text text)")

    def check_connection(func):
        @wraps(func)
        async def inner(self, *args, **kwargs):
            self.pool = self.pool or await self.setup()
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
        async with self.pool.acquire() as con:
            await con.execute('INSERT INTO vc_setting (guild_id, text_ch_id, vc_ch_id) VALUES ($1, $2, $3)', guild_id, text_ch_id, vc_ch_id)

    @check_connection
    async def get_vc_setting(self, guild_id: int):
        async with self.pool.acquire() as con:
            data = await con.fetch('SELECT * FROM vc_setting WHERE guild_id = $1', guild_id)
        return data


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
