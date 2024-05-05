import discord
from discord import app_commands, ui
from discord.ext import commands


class Setting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.guild_only()
    class SettingsGroup(app_commands.Group):
        pass

    settings_group = SettingsGroup(name='設定', description='設定に関するコマンド')

    @settings_group.command(name='vc参加したときに通知')
    async def cmd_setting(self, interaction: discord.Interaction):
        """設定を表示するコマンドです"""
        embed = discord.Embed(title='設定')
        embed.add_field(name='設定1', value='設定1の説明', inline=False)
        embed.add_field(name='設定2', value='設定2の説明', inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Setting(bot))
