import discord
from discord import app_commands, ui, Colour, ButtonStyle, SelectOption, Object
from discord.ext import commands


class Setting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='設定')
    async def cmd_setting(self, interaction: discord.Interaction):
        """各種設定を行います。"""
        await interaction.response.defer(ephemeral=True)

        data = await self.bot.db.get_notice_function(interaction.guild.id)
        view = SettingView(data, self.bot.db)

        return await interaction.followup.send(view=view, ephemeral=True)


class BackToSettingButton(ui.Button):
    def __init__(self):
        super().__init__(label='最初に戻る', style=ButtonStyle.gray)

    async def callback(self, interaction: discord.Interaction):
        data = await interaction.client.db.get_notice_function(interaction.guild.id)
        view = SettingView(data, interaction.client.db)
        await interaction.response.edit_message(view=view)


class SettingView(ui.LayoutView):

    def __init__(self, function_data, db):
        super().__init__()
        container = ui.Container(
            ui.TextDisplay(content="# VC入退出通知-設定"),
            ui.TextDisplay(content='### VC入退出通知の設定を行います。\n以下の各項目から設定を行ってください。'),
            ui.Separator(),
            ui.Section(
                ui.TextDisplay(content=f'➊ 本機能 - **{"有効" if function_data else "無効"}**'),
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
            ui.Section(
                ui.TextDisplay(content='➍ メンションするロールの設定'),
                accessory=NoticeRoleSetButton(db)
            ),
            ui.Section(
              ui.TextDisplay(content='➎ 除外するVCの設定'),
                accessory=NoticeExclusionSetButton(db)
            ),
            ui.Separator(),
            ui.Section(
                ui.TextDisplay(content='⚠️ 設定の初期化'),
                accessory=NoticeSettingResetButtonOnView(db)
            ),
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
            SelectOption(label='一つのチャンネル', description='通知のメッセージを一つのチャンネルに送信します', value='single', default=True if data else False),
            SelectOption(label='各VCのテキストチャット', description='通知のメッセージを各VCのテキストチャットに送信します', value='vc_text', default=True if not data else False),
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
            disabled=False if data else True,
            default_values=[Object(data.get('single_channel_id'))] if data and data.get('single_channel_id') else None,
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


class NoticeRoleSetButton(ui.Button):
    def __init__(self, db):
        self.db = db
        super().__init__(label='④', style=ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        data = await self.db.get_notice_role_setting(interaction.guild.id)
        view = NoticeRoleView(data, self.db)
        await interaction.response.edit_message(view=view)


class NoticeRoleView(ui.LayoutView):
    row = ui.ActionRow()
    row.add_item(BackToSettingButton())

    def __init__(self, data, db):
        super().__init__()

        container = ui.Container(
            ui.TextDisplay(content="# 通知ロール設定"),
            ui.TextDisplay(content='### メンションするロールを設定します。'),
            ui.Separator(),
            ui.TextDisplay(content=f'設定の有効/無効'),
            NoticeRoleBoolActionRow(NoticeRoleBoolButton(data, db)),
            ui.Separator(),
            ui.TextDisplay(content=f'通知ロール'),
            NoticeRoleActionRow(NoticeRoleTypeSelect(data, db)),
            accent_color=Colour.green(),
        )
        self.add_item(container)
        self.remove_item(self.row)
        self.add_item(self.row)


class NoticeRoleActionRow(ui.ActionRow):
    def __init__(self, select):
        super().__init__()
        self.add_item(select)

class NoticeRoleBoolActionRow(ui.ActionRow):
    def __init__(self, button):
        super().__init__()
        self.add_item(button)


class NoticeRoleBoolButton(ui.Button):
    def __init__(self, data, db):
        self.db = db
        super().__init__(
            style=discord.ButtonStyle.green if data else discord.ButtonStyle.gray,
            label="有効" if data else "無効"
        )

    async def callback(self, interaction: discord.Interaction):
        data = await self.db.get_notice_role_setting(interaction.guild.id)

        if not data:
            await self.db.toggle_notice_role_bool(interaction.guild.id, False)
        else:
            await self.db.toggle_notice_role_bool(interaction.guild.id, True)

        data = await self.db.get_notice_role_setting(interaction.guild.id)
        view = NoticeRoleView(data, self.db)
        await interaction.response.edit_message(view=view)


class NoticeRoleTypeSelect(ui.RoleSelect):
    def __init__(self, data, db):
        self.db = db
        super().__init__(
            placeholder='メンションするロールを選択してください。',
            custom_id='notice_role_select',
            min_values=1,
            max_values=1,
            disabled=False if data else True,
            default_values=[Object(data.get('notice_role_id'))] if data and data.get('notice_role_id') else None,
        )

    async def callback(self, interaction: discord.Interaction):
        selected_role = self.values[0]
        await self.db.set_notice_role_setting(interaction.guild.id, selected_role.id)

        data = await self.db.get_notice_role_setting(interaction.guild.id)
        view = NoticeRoleView(data, self.db)
        await interaction.response.edit_message(view=view)

# -- 除外するVCの設定 START --

class NoticeExclusionSetButton(ui.Button):
    def __init__(self, db):
        self.db = db
        super().__init__(label='⑤', style=ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        data = await self.db.get_notice_exclusion_vc(interaction.guild.id)
        view = NoticeExclusionView(data, self.db)
        await interaction.response.edit_message(view=view)


class NoticeExclusionView(ui.LayoutView):
    row = ui.ActionRow()
    row.add_item(BackToSettingButton())

    def __init__(self, data, db):
        super().__init__()

        container = ui.Container(
            ui.TextDisplay(content="# 除外するVCの設定"),
            ui.TextDisplay(content='### 通知を除外するVCを設定します。'),
            ui.Separator(),
            ui.TextDisplay(content=f'以下のセレクトメニューから除外するVCを選択してください。\n現状設定できるのは最大25件です。'),
            NoticeExclusionActionRow(NoticeExclusionSelect(data, db)),
            ui.TextDisplay(content='※除外するVCに設定したVCでの入退出は通知されなくなります。'),
            accent_color=Colour.green(),
        )
        self.add_item(container)
        self.remove_item(self.row)
        self.add_item(self.row)


class NoticeExclusionActionRow(ui.ActionRow):
    def __init__(self, select):
        super().__init__()
        self.add_item(select)

class NoticeExclusionSelect(ui.ChannelSelect):
    def __init__(self, data, db):
        self.db = db
        self.data: list[int] = data
        super().__init__(
            placeholder='通知を除外するVCを選択してください。',
            channel_types=[discord.ChannelType.voice],
            custom_id='notice_exclusion_vc_select',
            min_values=0,
            max_values=25,
            default_values=[Object(vc_id) for vc_id in data] if data else None,
        )

    async def callback(self, interaction: discord.Interaction):
        old_data = self.data or []
        selected_vcs = self.values
        selected_vc_ids = [vc.id for vc in selected_vcs]

        append_ids = set(selected_vc_ids) - set(old_data)
        remove_ids = set(old_data) - set(selected_vc_ids)

        await self.db.set_notice_exclusion_vc(interaction.guild.id, append_ids)
        await self.db.remove_notice_exclusion_vc(remove_ids)

        data = await self.db.get_notice_exclusion_vc(interaction.guild.id)
        view = NoticeExclusionView(data, self.db)
        await interaction.response.edit_message(view=view)

# -- 除外するVCの設定 END --

# -- 初期化ボタン START --
class NoticeSettingResetButtonOnView(ui.Button):
    def __init__(self, db):
        self.db = db
        super().__init__(label='初期化', style=ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        view = NoticeSettingResetView(db=self.db)
        await interaction.response.edit_message(view=view)

class NoticeSettingResetButton:
    class Excute(ui.Button):
        def __init__(self, db):
            self.db = db
            super().__init__(label='実行', style=ButtonStyle.danger)

        async def callback(self, interaction: discord.Interaction):
            try:
                await self.db.reset_notice_setting(interaction.guild.id)
                await interaction.response.send_message(content='設定を初期化しました。', ephemeral=True)
                self.view.stop()
            except Exception as e:
                await interaction.response.send_message(
                    content=f'初期化に失敗しました。\n[公式サーバー](https://discord.gg/k5Feum44gE)までお問い合わせください。',
                    ephemeral=True)
                self.view.stop()

    class Cancel(ui.Button):
        def __init__(self):
            super().__init__(label='キャンセル', style=ButtonStyle.gray)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_message(content='キャンセルしました。', ephemeral=True)
            self.view.stop()


class NoticeSettingResetView(ui.LayoutView):
    row = ui.ActionRow()

    def __init__(self, db):
        super().__init__()

        container = ui.Container(
            ui.TextDisplay(content="## 本当に削除しますか"),
            ui.TextDisplay(content='この操作はこのサーバーの通知設定を初期化します。元に戻せません。'),
            accent_color=Colour.red(),
        )
        self.row.add_item(NoticeSettingResetButton.Excute(db=db))
        self.row.add_item(NoticeSettingResetButton.Cancel())
        self.add_item(container)
        self.remove_item(self.row)
        self.add_item(self.row)
# -- 初期化ボタン END --

async def setup(bot):
    await bot.add_cog(Setting(bot))
