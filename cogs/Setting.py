import discord
from discord import app_commands, ui, Colour, ButtonStyle, SelectOption, Object
from discord.ui import View
from discord.ext import commands


class Setting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='設定')
    async def cmd_setting(self, interaction: discord.Interaction):
        """各種設定を行います。"""
        data = await self.bot.db.get_notice_function(interaction.guild.id)
        view = SettingView(data, self.bot.db)
        return await interaction.response.send_message(view=view, ephemeral=True)


class BackToSettingButton(ui.Button):
    def __init__(self):
        super().__init__(label='最初に戻る', style=ButtonStyle.gray)

    async def callback(self, interaction: discord.Interaction):
        data = await interaction.client.db.get_notice_function(interaction.guild.id)
        view = SettingView(data, interaction.client.db)
        await interaction.response.edit_message(view=view)


class SettingView(ui.LayoutView):

    def __init__(self, data, db):
        super().__init__()
        container = ui.Container(
            ui.TextDisplay(content="# VC入退出通知-設定"),
            ui.TextDisplay(content='### VC入退出通知の設定を行います。\n以下の各項目から設定を行ってください。'),
            ui.Separator(),
            ui.Section(
                ui.TextDisplay(content=f'➊ 本機能 - **{"有効" if data else "無効"}**'),
                accessory=NoticeFunctionBoolButton(db)
            ),
            ui.Section(
                ui.TextDisplay(content='➋ 通知先チャンネルの設定'),
                accessory=NoticeChannelSetButton(db)
            ),
            ui.Section(
                ui.TextDisplay(content='➌ 通知する種類の設定'),
                accessory=NoticeTypeSetButton(db)
            ),
            ui.Separator(),
            accent_color=Colour.green(),
        )

        self.add_item(container)


class NoticeFunctionBoolButton(ui.Button):
    def __init__(self, db):
        self.db = db
        super().__init__(label='切替', style=ButtonStyle.gray)

    async def callback(self, interaction: discord.Interaction):
        # 機能の有効化/無効化切替処理
        new = await self.db.toggle_notice_function(interaction.guild.id)
        view = SettingView(new, self.db)
        await interaction.response.edit_message(view=view)


class NoticeChannelSetButton(ui.Button):
    def __init__(self, db):
        self.db = db
        super().__init__(label='⓶', style=ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        # 通知先チャンネル設定のUIへ遷移
        data = await self.db.get_notice_channel_type(interaction.guild.id)
        view = NoticeChannelView(data, self.db)
        await interaction.response.edit_message(view=view)


class NoticeChannelView(ui.LayoutView):
    row = ui.ActionRow()
    row.add_item(BackToSettingButton())

    def __init__(self, data, db):
        super().__init__()
        # ここに通知先チャンネル設定のUI要素を追加

        container = ui.Container(
            ui.TextDisplay(content="# 通知先チャンネル設定"),
            ui.TextDisplay(content='### 通知先チャンネルを設定します。'),
            ui.Separator(),
            ui.TextDisplay(content=f'通知チャンネル'),
            ui.TextDisplay(
                content='※各VCのテキストチャットを選択した場合、Botが各VCのテキストチャットを閲覧できる必要があります。'
            ),
            NoticeChannelActionRow(NoticeChannelTypeSelect(data, db)),
            ui.Separator(),
            ui.TextDisplay(content='チャンネル先設定'),
            ui.TextDisplay(
                content='※一つのチャンネルを選択した場合にのみ設定可能です。'
            ),
            NoticeChannelActionRow(NoticeChannelSelect(data, db)),
            accent_color=Colour.green(),
        )
        self.add_item(container)
        self.remove_item(self.row)
        self.add_item(self.row)


class NoticeChannelActionRow(ui.ActionRow):
    def __init__(self, select: ui.Select | ui.ChannelSelect):
        super().__init__()
        self.add_item(select)


class NoticeChannelTypeSelect(ui.Select):
    def __init__(self, data, db):
        self.db = db
        options = [
            SelectOption(label='一つのチャンネル', description='通知のメッセージを一つのチャンネルに送信します', value='single', default=True if data and data.get('channel_type') == 'single' else False),
            SelectOption(label='各VCのテキストチャット', description='通知のメッセージを各VCのテキストチャットに送信します', value='vc_text', default=True if data and data.get('channel_type') == 'vc_text' else False),
        ]
        super().__init__(placeholder='通知先を選択してください。', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_value = self.values[0]
        if selected_value == 'single':
            await self.db.set_notice_channel_type(interaction.guild.id, 'single')
        else:
            await self.db.set_notice_channel_type(interaction.guild.id, 'vc_text')

        data = await self.db.get_notice_channel_type(interaction.guild.id)
        view = NoticeChannelView(data, self.db)
        await interaction.response.edit_message(view=view)


class NoticeChannelSelect(ui.ChannelSelect):
    def __init__(self, data, db):
        self.db = db
        super().__init__(
            placeholder='通知を送信するチャンネルを選択してください。',
            channel_types=[discord.ChannelType.text],
            custom_id='notice_single_channel_select',
            min_values=1,
            max_values=1,
            disabled=False if data and data.get('channel_type') == 'single' else True,
            default_values=[Object(data.get('single_channel_id'))] if data and data.get(
                'channel_type') == 'single' and data.get('single_channel_id') else None,

        )

    async def callback(self, interaction: discord.Interaction):
        selected_channel = self.values[0]
        await self.db.set_notice_single_channel(interaction.guild.id, selected_channel.id)

        data = await self.db.get_notice_channel_type(interaction.guild.id)
        view = NoticeChannelView(data, self.db)
        await interaction.response.edit_message(view=view)


class NoticeTypeSetButton(ui.Button):
    def __init__(self, db):
        self.db = db
        super().__init__(label='⓷', style=ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        data = await self.db.get_all_notice_type_setting(interaction.guild.id)
        view = NoticeTypeView(data, self.db)
        await interaction.response.edit_message(view=view)


class NoticeTypeView(ui.LayoutView):
    row = ui.ActionRow()
    row.add_item(BackToSettingButton())

    def __init__(self, data, db):
        super().__init__()
        # ここに通知種類設定のUI要素を追加

        container = ui.Container(
            ui.TextDisplay(content="# 通知種類設定"),
            ui.TextDisplay(content='### 通知する種類を設定します。'),
            ui.Separator(),
            ui.Section(
                ui.TextDisplay(content=f'・VC参加通知 - {"ON" if data.get("notice_join") else "OFF"}'),
                accessory=VcNoticeToggleButton(vc_type="join", db=db)
            ),
            ui.Separator(),
            ui.Section(
                ui.TextDisplay(content=f'・VC退出通知 - {"ON" if data.get("notice_leave") else "OFF"}'),
                accessory=VcNoticeToggleButton(vc_type="leave", db=db)
            ),
            accent_color=Colour.green(),
        )
        self.add_item(container)
        self.remove_item(self.row)
        self.add_item(self.row)


class VcNoticeToggleButton(ui.Button):
    def __init__(self, vc_type: str, db):
        self.vc_type = vc_type
        self.db = db
        super().__init__(label='🔄️', style=ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        if self.vc_type == "join":
            # VC参加通知の切替処理
            new = await self.db.toggle_notice_type_join(interaction.guild.id)
        else:
            # VC退出通知の切替処理
            new = await self.db.toggle_notice_type_leave(interaction.guild.id)

        view = NoticeTypeView(new, self.db)
        await interaction.response.edit_message(view=view)


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
