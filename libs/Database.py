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
            # 全体機能の有効/無効
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS notice_function_bool (guild_id bigint NOT NULL PRIMARY KEY)"
            )
            # 入室時の通知 | テーブルが存在する：機能が有効、存在しない：機能が無効
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS notice_join_bool (guild_id bigint NOT NULL PRIMARY KEY)"
            )
            # 退室時の通知 | テーブルが存在する：機能が有効、存在しない：機能が無効
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS notice_leave_bool (guild_id bigint NOT NULL PRIMARY KEY)"
            )
            # 通知するチャンネルのタイプ(指定orVCテキストチャンネル) | テーブルが存在しない：VCテキストチャンネル
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS notice_channel_type_setting (guild_id bigint NOT NULL PRIMARY KEY, single_channel_id bigint)"
            )
            # メンションするロールの設定 | テーブルが存在しない：機能オフ
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS notice_role_setting (guild_id bigint NOT NULL PRIMARY KEY, notice_role_id bigint)"
            )
            # 除外するVCの設定
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS notice_exclusion_vc_setting (guild_id bigint NOT NULL, exclusion_vc_id bigint NOT NULL, PRIMARY KEY (exclusion_vc_id))"
            )

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
    async def get_notice_function(self, guild_id: int) -> bool:
        """本機能の有効無効を取得する関数"""
        async with self.pool.acquire() as con:
            data = await con.fetch('SELECT * FROM notice_function_bool WHERE guild_id = $1', guild_id)
            if not data:
                return False
            return True

    @check_connection
    async def toggle_notice_function(self, guild_id: int) -> bool:
        """機能全体のオン/オフを切り替える関数"""
        data = await self.get_notice_function(guild_id)
        async with self.pool.acquire() as con:
            if not data:
                await con.execute('INSERT INTO notice_function_bool (guild_id) VALUES ($1)', guild_id)
                return True
            else:
                await con.execute('DELETE FROM notice_function_bool WHERE guild_id = $1', guild_id)
                return False

    @check_connection
    async def get_notice_join_bool(self, guild_id: int) -> bool:
        """入室時の通知の有効/無効を取得する関数"""
        async with self.pool.acquire() as con:
            data = await con.fetch('SELECT * FROM notice_join_bool WHERE guild_id = $1', guild_id)
            if not data:
                return False
            return True

    @check_connection
    async def get_notice_leave_bool(self, guild_id: int) -> bool:
        """退室時の通知の有効/無効を取得する関数"""
        async with self.pool.acquire() as con:
            data = await con.fetch('SELECT * FROM notice_leave_bool WHERE guild_id = $1', guild_id)
            if not data:
                return False
            return True

    @check_connection
    async def get_all_notice_type_setting(self, guild_id: int) -> dict[str, bool]:
        """入室時と退室時のデータをまとめて取得"""
        l_data = await self.get_notice_leave_bool(guild_id)
        j_data = await self.get_notice_join_bool(guild_id)
        data = {
            "notice_join": j_data,
            "notice_leave": l_data
        }
        return data

    @check_connection
    async def toggle_notice_type_join(self, guild_id: int) -> dict[str, bool]:
        """入室時の通知の機能の有効無効を交互に変更する関数"""
        data = await self.get_notice_join_bool(guild_id)
        async with self.pool.acquire() as con:
            if not data:
                await con.execute('INSERT INTO notice_join_bool (guild_id) VALUES ($1)', guild_id)
            else:
                await con.execute('DELETE FROM notice_join_bool WHERE guild_id = $1', guild_id)

            new_data = await self.get_all_notice_type_setting(guild_id)
            return new_data

    @check_connection
    async def toggle_notice_type_leave(self, guild_id: int) -> dict[str, bool]:
        """退室時の通知の機能の有効無効を交互に変更する関数"""
        data = await self.get_notice_leave_bool(guild_id)
        async with self.pool.acquire() as con:
            if not data:
                await con.execute('INSERT INTO notice_leave_bool (guild_id) VALUES ($1)', guild_id)
            else:
                await con.execute('DELETE FROM notice_leave_bool WHERE guild_id = $1', guild_id)

            new_data = await self.get_all_notice_type_setting(guild_id)
            return new_data

    @check_connection
    async def get_notice_channel_type(self, guild_id: int):
        """送信するチャンネルの種類を取得する関数"""
        async with self.pool.acquire() as con:
            data = await con.fetch('SELECT * FROM notice_channel_type_setting WHERE guild_id = $1', guild_id)
            if not data:
                return None
            return data[0]

    @check_connection
    async def set_notice_channel_type(self, guild_id: int, channel_type: str):
        """送信するチャンネルの種類を設定する関数"""
        data = await self.get_notice_channel_type(guild_id)
        async with self.pool.acquire() as con:
            if data is None:
                if channel_type == 'single':
                    await con.execute('INSERT INTO notice_channel_type_setting (guild_id, single_channel_id) VALUES ($1, $2)', guild_id, 0)
            else:
                if channel_type == 'vc_text':
                    await con.execute('DELETE FROM notice_channel_type_setting WHERE guild_id = $1', guild_id)
            new = await self.get_notice_channel_type(guild_id)
            return new

    @check_connection
    async def set_notice_single_channel(self, guild_id: int, single_channel_id: int):
        """特定のチャンネルに通知する場合のチャンネルIDを保存する関数"""
        data = await self.get_notice_channel_type(guild_id)
        async with self.pool.acquire() as con:
            if data is None:
                await con.execute('INSERT INTO notice_channel_type_setting (guild_id, single_channel_id) VALUES ($1, $2)', guild_id, single_channel_id)
            else:
                await con.execute('UPDATE notice_channel_type_setting SET single_channel_id = $1 WHERE guild_id = $2', single_channel_id, guild_id)
            new = await self.get_notice_channel_type(guild_id)
            return new

    @check_connection
    async def get_notice_role_setting(self, guild_id: int):
        """ロールのメンションの機能の有効/無効を取得する関数"""
        async with self.pool.acquire() as con:
            data = await con.fetch('SELECT * FROM notice_role_setting WHERE guild_id = $1', guild_id)
            if not data:
                return None
            return data[0]

    @check_connection
    async def set_notice_role_setting(self, guild_id: int, role_id: int):
        """ロールのIDを設定する関数"""
        data = await self.get_notice_role_setting(guild_id)
        async with self.pool.acquire() as con:
            if data is None:
                await con.execute('INSERT INTO notice_role_setting (guild_id, notice_role_id) VALUES ($1, $2)', guild_id, role_id)
            else:
                await con.execute('UPDATE notice_role_setting SET notice_role_id = $1 WHERE guild_id = $2', role_id, guild_id)

            new = await self.get_notice_role_setting(guild_id)
            return new

    @check_connection
    async def toggle_notice_role_bool(self, guild_id: int, data_bool: bool):
        """ロールのメンションの有効/無効を切り替える関数"""
        async with self.pool.acquire() as con:
            if data_bool:
                await con.execute('DELETE FROM notice_role_setting WHERE guild_id = $1', guild_id)
            else:
                await con.execute('INSERT INTO notice_role_setting (guild_id, notice_role_id) VALUES ($1, $2)', guild_id, 0)

            new = await self.get_notice_role_setting(guild_id)
            return new

    @check_connection
    async def reset_notice_setting(self, guild_id: int):
        async with self.pool.acquire() as con:
            await con.execute('DELETE FROM notice_function_bool WHERE guild_id = $1', guild_id)
            await con.execute('DELETE FROM notice_join_bool WHERE guild_id = $1', guild_id)
            await con.execute('DELETE FROM notice_leave_bool WHERE guild_id = $1', guild_id)
            await con.execute('DELETE FROM notice_channel_type_setting WHERE guild_id = $1', guild_id)
            await con.execute('DELETE FROM notice_role_setting WHERE guild_id = $1', guild_id)
            await con.execute('DELETE FROM notice_exclusion_vc_setting WHERE guild_id = $1', guild_id)

    @check_connection
    async def get_notice_exclusion_vc(self, guild_id: int) -> list[int]:
        """除外するチャンネルのIDを取得する関数"""
        async with self.pool.acquire() as con:
            data = await con.fetch('SELECT exclusion_vc_id FROM notice_exclusion_vc_setting WHERE guild_id = $1', guild_id)
            if not data:
                return []
            return [record.get('exclusion_vc_id') for record in data]

    @check_connection
    async def set_notice_exclusion_vc(self, guild_id: int, append_exclusion_vc_ids: set[int]):
        """除外するチャンネルを設定する関数"""
        async with self.pool.acquire() as con:
            for exclusion_vc_id in append_exclusion_vc_ids:
                await con.execute('INSERT INTO notice_exclusion_vc_setting (guild_id, exclusion_vc_id) VALUES ($1, $2) ON CONFLICT DO NOTHING', guild_id, exclusion_vc_id)

    @check_connection
    async def remove_notice_exclusion_vc(self, remove_exclusion_vc_ids: set[int]):
        """除外するチャンネルを削除する関数"""
        async with self.pool.acquire() as con:
            for remove_exclusion_vc_id in remove_exclusion_vc_ids:
                await con.execute('DELETE FROM notice_exclusion_vc_setting WHERE exclusion_vc_id = $1', remove_exclusion_vc_id)


class DebugDatabase(ProductionDatabase):
    def __init__(self):
        super().__init__()

    async def execute(self, sql):
        logging.info(f"executing sql: {sql}")

    async def fetch(self, sql):
        logging.info(f"fetching by sql: {sql}")

    async def set_vc_setting(self, guild_id: int, text_ch_id: int, vc_ch_id: int):
        pass


if env.DEBUG:
    Database = DebugDatabase
else:
    Database = ProductionDatabase
