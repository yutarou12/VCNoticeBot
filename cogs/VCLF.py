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
        if member.id == self.bot.user.id and after.channel is None:
            return await self.db.del_vc_setting(member.guild.id)

        if member.bot:
            return None

        guild_bool = await self.db.get_notice_function(member.guild.id)
        if not guild_bool:
            return None

        # 送信チャンネルの種類の取得
        guild_data = await self.db.get_notice_channel_type(member.guild.id)
        if not guild_data:
            channel_type = "vc_text"
        else:
            channel_type = guild_data.get('channel_type')

        # VC入室時
        if after.channel is not None and before.channel is None:
            join_bool = await self.db.get_notice_join_bool(member.guild.id)
            if not join_bool:
                return None
            if channel_type == "vc_text":
                ch = after.channel
            else:
                vc_notice_id = guild_data.get('single_channel_id')
                if not vc_notice_id:
                    return None
                ch = member.guild.get_channel(vc_notice_id)
            if not ch:
                return None

            notice_role_bool = await self.db.get_notice_role_bool(member.guild.id)
            if not notice_role_bool:
                return await ch.send(f'> 📥 {member.mention} が {after.channel.mention} に参加しました。 <t:{math.floor(datetime.datetime.now(datetime.timezone.utc).timestamp())}:T>', allowed_mentions=discord.AllowedMentions(users=False))
            else:
                notice_role_data = await self.db.get_notice_role_setting(member.guild.id)
                notice_role_id = notice_role_data.get('notice_role_id')
                notice_role: discord.Role = member.guild.get_role(notice_role_id)
                if not notice_role:
                    return await ch.send(f'> 📥 {member.mention} が {after.channel.mention} に参加しました。 <t:{math.floor(datetime.datetime.now(datetime.timezone.utc).timestamp())}:T>', allowed_mentions=discord.AllowedMentions(users=False))
                else:
                    return await ch.send(f'{notice_role.mention}\n> 📥 {member.mention} が {after.channel.mention} に参加しました。 <t:{math.floor(datetime.datetime.now(datetime.timezone.utc).timestamp())}:T>', allowed_mentions=discord.AllowedMentions(users=False))

        # VC退出時
        elif before.channel is not None and after.channel is None:
            leave_bool = await self.db.get_notice_leave_bool(member.guild.id)
            if not leave_bool:
                return None
            if channel_type == "vc_text":
                ch = before.channel
            else:
                vc_notice_id = guild_data.get('single_channel_id')
                if not vc_notice_id:
                    return None
                ch = member.guild.get_channel(vc_notice_id)
            if not ch:
                return None
            notice_role_bool = await self.db.get_notice_role_bool(member.guild.id)
            if not notice_role_bool:
                return await ch.send(f'> 📤 {member.mention} が {before.channel.mention} から退出しました。 <t:{math.floor(datetime.datetime.now(datetime.timezone.utc).timestamp())}:T>', allowed_mentions=discord.AllowedMentions(users=False))
            else:
                notice_role_data = await self.db.get_notice_role_setting(member.guild.id)
                notice_role_id = notice_role_data.get('notice_role_id')
                notice_role: discord.Role = member.guild.get_role(notice_role_id)
                if not notice_role:
                    return await ch.send(f'> 📤 {member.mention} が {before.channel.mention} から退出しました。 <t:{math.floor(datetime.datetime.now(datetime.timezone.utc).timestamp())}:T>', allowed_mentions=discord.AllowedMentions(users=False))
                else:
                    return await ch.send(f'{notice_role.mention}\n> 📤 {member.mention} が {before.channel.mention} から退出しました。 <t:{math.floor(datetime.datetime.now(datetime.timezone.utc).timestamp())}:T>', allowed_mentions=discord.AllowedMentions(users=False))

        return None


async def setup(bot):
    await bot.add_cog(VCLF(bot))
