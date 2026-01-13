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
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS notice_type_setting (guild_id bigint NOT NULL PRIMARY KEY, notice_join BOOLEAN NOT NULL, notice_leave BOOLEAN NOT NULL)")
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS notice_channel_type_setting (guild_id bigint NOT NULL PRIMARY KEY, channel_type TEXT NOT NULL, single_channel_id bigint)")
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS notice_function_bool (guild_id bigint NOT NULL PRIMARY KEY)")

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
    async def get_notice_vc_channel(self, guild_id: int):
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

    @check_connection
    async def get_notice_function(self, guild_id: int):
        data = await self.fetch(f'SELECT * FROM notice_function_bool WHERE guild_id = {guild_id}')
        if not data:
            return None
        return data[0]

    @check_connection
    async def toggle_notice_function(self, guild_id: int):
        data = await self.get_notice_function(guild_id)
        if data is None:
            await self.execute(f'INSERT INTO notice_function_bool (guild_id) VALUES ({guild_id})')
            return True
        else:
            await self.execute(f'DELETE FROM notice_function_bool WHERE guild_id = {guild_id}')
            return False

    @check_connection
    async def get_notice_join_bool(self, guild_id: int):
        async with self.pool.acquire() as con:
            data = await con.fetch('SELECT notice_join FROM notice_type_setting WHERE guild_id = $1', guild_id)
            if not data:
                return None
            return data[0].get('notice_join')

    @check_connection
    async def get_notice_leave_bool(self, guild_id: int):
        async with self.pool.acquire() as con:
            data = await con.fetch('SELECT notice_leave FROM notice_type_setting WHERE guild_id = $1', guild_id)
            if not data:
                return None
            return data[0].get('notice_leave')

    @check_connection
    async def get_all_notice_type_setting(self, guild_id: int):
        l_data = await self.get_notice_leave_bool(guild_id)
        j_data = await self.get_notice_join_bool(guild_id)
        data = {
            "notice_join": j_data if j_data else None,
            "notice_leave": l_data if l_data else None
        }
        return data

    @check_connection
    async def toggle_notice_type_join(self, guild_id: int):
        data = await self.get_notice_join_bool(guild_id)
        if data is None:
            await self.execute(f'INSERT INTO notice_type_setting (guild_id, notice_join, notice_leave) VALUES ({guild_id}, TRUE, FALSE)')
        else:
            new_value = not data
            await self.execute(f'UPDATE notice_type_setting SET notice_join = {new_value} WHERE guild_id = {guild_id}')

        new_data = await self.get_all_notice_type_setting(guild_id)
        return new_data

    @check_connection
    async def toggle_notice_type_leave(self, guild_id: int):
        data = await self.get_notice_leave_bool(guild_id)
        if data is None:
            await self.execute(f'INSERT INTO notice_type_setting (guild_id, notice_join, notice_leave) VALUES ({guild_id}, FALSE, TRUE)')
        else:
            new_value = not data
            await self.execute(f'UPDATE notice_type_setting SET notice_leave = {new_value} WHERE guild_id = {guild_id}')

        new_data = await self.get_all_notice_type_setting(guild_id)
        return new_data

    @check_connection
    async def get_notice_channel_type(self, guild_id: int):
        data = await self.fetch(f'SELECT * FROM notice_channel_type_setting WHERE guild_id = {guild_id}')
        if not data:
            return None
        return data[0]

    @check_connection
    async def set_notice_channel_type(self, guild_id: int, channel_type: str):
        data = await self.get_notice_channel_type(guild_id)
        if data is None:
            if channel_type == 'single':
                await self.execute(f'INSERT INTO notice_channel_type_setting (guild_id, channel_type, single_channel_id) VALUES ({guild_id}, \'{channel_type}\', {0})')
            else:
                await self.execute(f'INSERT INTO notice_channel_type_setting (guild_id, channel_type) VALUES ({guild_id}, \'{channel_type}\')')
        else:
            if channel_type == 'single':
                await self.execute(f'UPDATE notice_channel_type_setting SET channel_type = \'{channel_type}\' WHERE guild_id = {guild_id}')
            else:
                await self.execute(f'UPDATE notice_channel_type_setting SET channel_type = \'{channel_type}\' WHERE guild_id = {guild_id}')
        new = await self.get_notice_channel_type(guild_id)
        return new

    @check_connection
    async def set_notice_single_channel(self, guild_id: int, single_channel_id: int):
        data = await self.get_notice_channel_type(guild_id)
        if data is None:
            await self.execute(f'INSERT INTO notice_channel_type_setting (guild_id, channel_type, single_channel_id) VALUES ({guild_id}, \'single\', {single_channel_id})')
        else:
            await self.execute(f'UPDATE notice_channel_type_setting SET single_channel_id = {single_channel_id} WHERE guild_id = {guild_id}')
        new = await self.get_notice_channel_type(guild_id)
        return new


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
