import datetime
import math

import discord
from discord import app_commands
from discord.ext import commands


class VCLF(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db

    @app_commands.command(name='参加')
    @app_commands.guild_only()
    async def cmd_vclf(self, interaction: discord.Interaction):
        """参加する"""

        if not interaction.user.voice:
            return await interaction.response.send_message('VCに参加してからコマンドを実行してください。', ephemeral=True)
        await interaction.guild.change_voice_state(channel=interaction.user.voice.channel, self_deaf=True)

        await self.db.set_vc_setting(interaction.guild.id, interaction.channel.id, interaction.user.voice.channel.id)

        return await interaction.response.send_message('参加しました。', ephemeral=True)

    @app_commands.command(name='退出')
    @app_commands.guild_only()
    async def cmd_vclf_leave(self, interaction: discord.Interaction):
        """退出する"""

        await interaction.guild.change_voice_state(channel=None)
        await self.db.del_vc_setting(interaction.guild.id)
        return await interaction.response.send_message('退出しました。', ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        if not await self.db.get_vc_setting(member.guild.id):
            return

        vc_ch_id = await self.db.get_vc_setting(member.guild.id).get("vc_ch_id")
        text_ch_id = await self.db.get_vc_setting(member.guild.id).get("text_ch_id")
        vc_ch = member.guild.get_channel(vc_ch_id)

        if before.channel is None and member in after.channel.members and after.channel == vc_ch:
            ch = member.guild.get_channel(text_ch_id)
            if not ch:
                return
            await ch.send(f'> 📥{member.mention} がVCに参加しました。 <t:{math.floor(datetime.datetime.utcnow().timestamp())}:T>', allowed_mentions=discord.AllowedMentions(users=False))

        if before.channel == vc_ch and after.channel is None:
            vc_ch: discord.VoiceChannel = vc_ch
            if len(vc_ch.members) == 1:
                return await member.guild.change_voice_state(channel=None)
            else:
                ch = member.guild.get_channel(text_ch_id)
                if not ch:
                    return
                await ch.send(f'> 📤{member.mention} がVCから退出しました。 <t:{math.floor(datetime.datetime.utcnow().timestamp())}:T>', allowed_mentions=discord.AllowedMentions(users=False))


async def setup(bot):
    await bot.add_cog(VCLF(bot))
