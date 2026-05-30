import datetime
import math
import asyncpg

import discord
from discord import app_commands
from discord.ext import commands


class VCLF(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after: discord.VoiceState):
        if member.bot:
            return None

        # 設定の有効/無効の取得
        if not await self.db.get_notice_function(member.guild.id):
            return None

        # 送信チャンネルの種類の取得
        guild_channel_type_data = await self.db.get_notice_channel_type(member.guild.id)

        # 休止チャンネルの取得
        if member.guild.afk_channel and member.guild.afk_channel == after.channel:
            return None

        # VC入室時
        if after.channel is not None and before.channel is None:
            # 休止チャンネルに入室の場合通知しない
            if member.guild.afk_channel and member.guild.afk_channel == after.channel:
                return None

            join_bool = await self.db.get_notice_join_bool(member.guild.id)
            if not join_bool:
                return None

            if not guild_channel_type_data:
                ch = after.channel
            else:
                vc_notice_id = guild_channel_type_data.get('single_channel_id')
                if not vc_notice_id:
                    return None
                ch = member.guild.get_channel(vc_notice_id)

            if not ch:
                return None

            notice_role_data = await self.db.get_notice_role_setting(member.guild.id)
            if not notice_role_data:
                return await ch.send(f'> 📥 {member.mention} が {after.channel.mention} に参加しました。 <t:{math.floor(datetime.datetime.now(datetime.timezone.utc).timestamp())}:T>', allowed_mentions=discord.AllowedMentions(users=False))
            else:
                notice_role_id = notice_role_data.get('notice_role_id')
                if not notice_role_id:
                    return None
                notice_role: discord.Role = member.guild.get_role(notice_role_id)
                if not notice_role:
                    return await ch.send(f'> 📥 {member.mention} が {after.channel.mention} に参加しました。 <t:{math.floor(datetime.datetime.now(datetime.timezone.utc).timestamp())}:T>', allowed_mentions=discord.AllowedMentions(users=False))
                else:
                    return await ch.send(f'{notice_role.mention}\n> 📥 {member.mention} が {after.channel.mention} に参加しました。 <t:{math.floor(datetime.datetime.now(datetime.timezone.utc).timestamp())}:T>', allowed_mentions=discord.AllowedMentions(users=False))

        # VC退出時
        elif before.channel is not None and after.channel is None:
            # 休止チャンネルから退室の場合通知しない
            if member.guild.afk_channel and member.guild.afk_channel == before.channel:
                return None

            leave_bool = await self.db.get_notice_leave_bool(member.guild.id)
            if not leave_bool:
                return None

            if not guild_channel_type_data:
                ch = before.channel
            else:
                vc_notice_id = guild_channel_type_data.get('single_channel_id')
                if not vc_notice_id:
                    return None
                ch = member.guild.get_channel(vc_notice_id)

            if not ch:
                return None

            notice_role_data = await self.db.get_notice_role_setting(member.guild.id)
            if not notice_role_data:
                return await ch.send(f'> 📤 {member.mention} が {before.channel.mention} から退出しました。 <t:{math.floor(datetime.datetime.now(datetime.timezone.utc).timestamp())}:T>', allowed_mentions=discord.AllowedMentions(users=False))
            else:
                notice_role_id = notice_role_data.get('notice_role_id')
                if not notice_role_id:
                    return None
                notice_role: discord.Role = member.guild.get_role(notice_role_id)
                if not notice_role:
                    return await ch.send(f'> 📤 {member.mention} が {before.channel.mention} から退出しました。 <t:{math.floor(datetime.datetime.now(datetime.timezone.utc).timestamp())}:T>', allowed_mentions=discord.AllowedMentions(users=False))
                else:
                    return await ch.send(f'{notice_role.mention}\n> 📤 {member.mention} が {before.channel.mention} から退出しました。 <t:{math.floor(datetime.datetime.now(datetime.timezone.utc).timestamp())}:T>', allowed_mentions=discord.AllowedMentions(users=False))

        return None


async def setup(bot):
    await bot.add_cog(VCLF(bot))
