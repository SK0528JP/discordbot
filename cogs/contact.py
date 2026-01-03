import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import re

# --- [TACTICAL CONSTANTS] ---
# 司令官（管理者）ID
ADMIN_ID = 840821281838202880
# ログ出力用チャンネルID
LOG_CHANNEL_ID = 1456893009273553017

# --- [UI: INTERACTIVE REPLY SYSTEM] ---
class ContactReplyView(discord.ui.View):
    """
    受信者が「返信」を行うためのボタンUI。
    このViewは永続化（timeout=None）され、Bot再起動後も動作しませんが、
    Botが起きている間は機能します。
    """
    def __init__(self, bot, sender_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.sender_id = sender_id

    @discord.ui.button(label="返信 (実名)", style=discord.ButtonStyle.success, emoji="👤", custom_id="contact:reply_pub")
    async def reply_public(self, it: discord.Interaction, button: discord.ui.Button):
        # 返信ボタンが押されたら、Modalを立ち上げる
        try:
            target = await self.bot.fetch_user(self.sender_id)
            await it.response.send_modal(ReplyModal(self.bot, target, False))
        except discord.NotFound:
            await it.response.send_message("❌ 返信先のユーザーが見つかりません（退会済み等の可能性があります）。", ephemeral=True)

    @discord.ui.button(label="返信 (匿名)", style=discord.ButtonStyle.secondary, emoji="🕶️", custom_id="contact:reply_anon")
    async def reply_anonymous(self, it: discord.Interaction, button: discord.ui.Button):
        try:
            target = await self.bot.fetch_user(self.sender_id)
            await it.response.send_modal(ReplyModal(self.bot, target, True))
        except discord.NotFound:
            await it.response.send_message("❌ 返信先のユーザーが見つかりません。", ephemeral=True)

class ReplyModal(discord.ui.Modal):
    """返信メッセージを入力するためのポップアップウィンドウ"""
    def __init__(self, bot, target_user, is_anonymous):
        super().__init__(title="匿名返信" if is_anonymous else "返信を作成")
        self.bot = bot
        self.target_user = target_user
        self.is_anonymous = is_anonymous
        
        self.message = discord.ui.TextInput(
            label="メッセージ内容",
            style=discord.TextStyle.paragraph,
            placeholder="ここに返信を入力してください...",
            required=True,
            max_length=2000
        )
        self.add_item(self.message)

    async def on_submit(self, it: discord.Interaction):
        await it.response.defer(ephemeral=True)

        # 返信Embedの作成
        color = 0x95a5a6 if self.is_anonymous else 0x2ecc71
        sender_name = "🕶️ 匿名ユーザー" if self.is_anonymous else it.user.name
        icon_url = "https://cdn.discordapp.com/embed/avatars/0.png" if self.is_anonymous else it.user.display_avatar.url
        footer_text = "Source: Unknown (Reply)" if self.is_anonymous else f"Source: {it.guild.name if it.guild else 'DM'} (Reply)"

        embed = discord.Embed(
            title="↩️ 返信を受信しました",
            description=self.message.value,
            color=color,
            timestamp=datetime.now()
        )
        embed.set_author(name=sender_name, icon_url=icon_url)
        embed.set_footer(text=f"Rb m/25 Relay System | {footer_text}")

        # 返信の返信（ラリー）ができるように、再度Viewを付与
        view = ContactReplyView(self.bot, it.user.id)

        try:
            await self.target_user.send(embed=embed, view=view)
            await it.followup.send("✅ 返信を送信しました。", ephemeral=True)
            
            # ログ出力（返信もログに残す）
            log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    title="🔄 [LOG] Reply Sent",
                    description=f"**From**: {it.user.name} (`{it.user.id}`)\n**To**: {self.target_user.name} (`{self.target_user.id}`)\n**Mode**: {'Anonymous' if self.is_anonymous else 'Public'}",
                    color=0xe67e22,
                    timestamp=datetime.now()
                )
                log_embed.add_field(name="Content", value=self.message.value[:1000], inline=False)
                await log_channel.send(embed=log_embed)

        except discord.Forbidden:
            await it.followup.send("❌ 相手のDMが閉じているため、返信できませんでした。", ephemeral=True)
        except Exception as e:
            await it.followup.send(f"❌ 返信エラー: {e}", ephemeral=True)


# --- [MAIN COG] ---
class Contact(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger
        self.bl_key = "contact_blacklist"
        
        # Ledgerからブラックリストを読み込む (データがない場合は空リスト)
        # JSON保存時はリストだが、高速処理のためメモリ内ではset(集合)として扱う
        if self.ledger:
            raw_data = self.ledger.data.get(self.bl_key, [])
            self.blacklist = set(int(uid) for uid in raw_data if str(uid).isdigit())
        else:
            self.blacklist = set()

    def _save_blacklist(self):
        """ブラックリストの変更をGist(Ledger)に即時保存する"""
        if self.ledger:
            self.ledger.data[self.bl_key] = list(self.blacklist)
            self.ledger.save()

    # --- Admin: Blacklist Management ---
    blacklist_group = app_commands.Group(name="contact_admin_blacklist", description="[Admin Only] Contact機能のブラックリスト管理")

    @blacklist_group.command(name="add", description="指定ユーザーをブラックリストに追加")
    async def bl_add(self, it: discord.Interaction, user_id: str):
        if it.user.id != ADMIN_ID:
            await it.response.send_message("❌ 権限がありません。", ephemeral=True)
            return
        
        # 数字以外の文字を除去してID抽出
        uid_str = re.sub(r'\D', '', user_id)
        if not uid_str:
            await it.response.send_message("❌ 無効なIDフォーマットです。", ephemeral=True)
            return

        uid = int(uid_str)
        if uid not in self.blacklist:
            self.blacklist.add(uid)
            self._save_blacklist()
            await it.response.send_message(f"🚫 ID: `{uid}` をブラックリストに追加・保存しました。", ephemeral=True)
        else:
            await it.response.send_message(f"ℹ️ ID: `{uid}` は既にブラックリストに存在します。", ephemeral=True)

    @blacklist_group.command(name="remove", description="指定ユーザーをブラックリストから削除")
    async def bl_remove(self, it: discord.Interaction, user_id: str):
        if it.user.id != ADMIN_ID:
            await it.response.send_message("❌ 権限がありません。", ephemeral=True)
            return

        uid_str = re.sub(r'\D', '', user_id)
        if not uid_str:
            await it.response.send_message("❌ 無効なIDです。", ephemeral=True)
            return
            
        uid = int(uid_str)
        if uid in self.blacklist:
            self.blacklist.remove(uid)
            self._save_blacklist()
            await it.response.send_message(f"⭕ ID: `{uid}` のブラックリストを解除・保存しました。", ephemeral=True)
        else:
            await it.response.send_message(f"❓ ID: `{uid}` はリストに登録されていません。", ephemeral=True)

    @blacklist_group.command(name="list", description="ブラックリスト一覧を表示")
    async def bl_list(self, it: discord.Interaction):
        if it.user.id != ADMIN_ID:
            await it.response.send_message("❌ 権限がありません。", ephemeral=True)
            return
        
        if not self.blacklist:
            await it.response.send_message("📋 ブラックリストは現在空です。", ephemeral=True)
        else:
            members = "\n".join([f"- `{uid}`" for uid in self.blacklist])
            await it.response.send_message(f"📋 **ブラックリスト登録済みID** ({len(self.blacklist)}):\n{members}", ephemeral=True)


    # --- User: Contact Command ---
    async def destination_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        choices = [app_commands.Choice(name="👑 開発者/管理者 (To Developer)", value="dev")]
        if current.isdigit():
            choices.append(app_commands.Choice(name=f"👤 User ID: {current}", value=current))
        return choices

    @app_commands.command(name="contact", description="指定した相手、または管理者にメッセージとファイルを送信します")
    @app_commands.describe(
        destination="宛先 (ID、メンション、または 'dev')",
        show_identity="送信者の情報を開示するか (True: 開示 / False: 匿名)",
        message="内容文 (添付ファイルのみの場合は '.' 等)",
        attachment="添付ファイル (画像/動画/文書など 1つまで)"
    )
    @app_commands.autocomplete(destination=destination_autocomplete)
    async def send_contact(
        self, 
        it: discord.Interaction, 
        destination: str, 
        show_identity: bool, 
        message: str,
        attachment: discord.Attachment = None
    ):
        # 1. ブラックリストチェック
        if it.user.id in self.blacklist:
            await it.response.send_message("🚫 **ACCESS DENIED**: あなたの通信権限は凍結されています。", ephemeral=True)
            return

        await it.response.defer(ephemeral=True)
        target_user = None

        # 2. 宛先解析 (Target Targeting)
        # A. 管理者宛
        if destination.lower() in ["dev", "admin", "owner", "開発者", "管理者"]:
            target_user = await self.bot.fetch_user(ADMIN_ID)
        # B. ユーザー指定
        else:
            clean_id = re.sub(r'\D', '', destination)
            if clean_id.isdigit():
                try:
                    target_user = await self.bot.fetch_user(int(clean_id))
                except discord.NotFound:
                    await it.followup.send("❌ 指定されたユーザーが見つかりません。", ephemeral=True)
                    return
                except Exception:
                    await it.followup.send("❌ ユーザー情報の取得に失敗しました。", ephemeral=True)
                    return
            else:
                await it.followup.send("❌ 宛先の形式が不正です。", ephemeral=True)
                return

        # Bot自身への送信防止
        if target_user.bot:
            await it.followup.send("❌ Botに対してメッセージを送信することはできません。", ephemeral=True)
            return

        # 3. メッセージ構築 (Payload)
        color = 0x2ecc71 if show_identity else 0x4C566A
        title = "📩 通信を受信しました"
        
        embed = discord.Embed(title=title, description=message, color=color, timestamp=datetime.now())
        
        if show_identity:
            embed.set_author(name=f"送信者: {it.user.name}", icon_url=it.user.display_avatar.url)
            embed.set_footer(text=f"ID: {it.user.id} | Source: {it.guild.name if it.guild else 'DM'}")
        else:
            embed.set_author(name="🕶️ 匿名ユーザー", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
            embed.set_footer(text="Source: Classified (Encrypted)")

        # 4. ファイル処理
        file_payload = None
        if attachment:
            file_payload = await attachment.to_file()
            if attachment.content_type and attachment.content_type.startswith("image"):
                embed.set_image(url=f"attachment://{attachment.filename}")

        # 5. 返信用View (ボタン) の作成
        # 受信者がボタンを押したときに、送信者(it.user.id)へ返信できるようにする
        view = ContactReplyView(self.bot, it.user.id)

        # 6. 送信実行 & ログ出力
        try:
            if file_payload:
                await target_user.send(embed=embed, file=file_payload, view=view)
            else:
                await target_user.send(embed=embed, view=view)
            
            dest_name = "管理者" if target_user.id == ADMIN_ID else target_user.name
            await it.followup.send(f"✅ **{dest_name}** へメッセージを転送しました。", ephemeral=True)

            # ログチャンネルへ転送
            log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    title="📡 [LOG] Contact Sent",
                    description=f"**From**: {it.user.name} (`{it.user.id}`)\n**To**: {dest_name} (`{target_user.id}`)\n**Mode**: {'Public' if show_identity else 'Anonymous'}",
                    color=0x3498db,
                    timestamp=datetime.now()
                )
                log_embed.add_field(name="Content", value=message[:1000], inline=False)
                if attachment:
                    log_embed.add_field(name="Attachment", value=attachment.url, inline=False)
                await log_channel.send(embed=log_embed)

        except discord.Forbidden:
            await it.followup.send("❌ 相手のDMが閉じられているため、送信できませんでした。", ephemeral=True)
        except Exception as e:
            await it.followup.send(f"❌ 送信エラー: {e}", ephemeral=True)

async def setup(bot):
    # main.py のグローバル変数 ledger_instance を取得してCogに渡す
    from __main__ import ledger_instance
    await bot.add_cog(Contact(bot, ledger_instance))
