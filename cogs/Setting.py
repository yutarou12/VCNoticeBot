import discord
from discord import app_commands
from discord.ui import View
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
        """VC参加したときに通知するか設定します。"""
        guild_data = await self.bot.db.get_notice_setting(interaction.guild.id)
        if not guild_data:
            gd = False
        else:
            gd = guild_data.get('notice_vc')
        embed = discord.Embed(title='VC参加通知設定', description='VC参加したときに通知するか設定します。')
        embed.add_field(name='今の設定', value="通知する" if gd else "通知しない", inline=False)

        view = VcNoticeView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        await view.wait()
        if view.value is None:
            return
        elif view.value:
            await self.bot.db.update_notice_setting(interaction.guild.id, True)
        else:
            await self.bot.db.update_notice_setting(interaction.guild.id, False)


class VcNoticeView(View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = None

    @discord.ui.button(label='通知ON', style=discord.ButtonStyle.green)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content='通知をオンにしました。', embed=None, view=None)
        self.value = True
        self.stop()

    @discord.ui.button(label='通知OFF', style=discord.ButtonStyle.gray)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message('通知をオフにしました。', embed=None, ephemeral=True)
        self.value = False
        self.stop()

    @discord.ui.button(label='キャンセル', style=discord.ButtonStyle.gray)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message('キャンセルしました。', embed=None, ephemeral=True)
        self.value = None
        self.stop()


async def setup(bot):
    await bot.add_cog(Setting(bot))
