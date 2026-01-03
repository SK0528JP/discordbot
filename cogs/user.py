import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import re

# システム定数
MAIN_GUILD_ID = 1372567395419291698
ADMIN_ID = 840821281838202880

class User(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    # --- ヘルパー: バッジ解析 ---
    def get_user_badges(self, user):
        badges = []
        flags = user.public_flags
        
        if flags.staff: badges.append("🛠️ Discordスタッフ")
        if flags.partner: badges.append("🤝 パートナー")
        if flags.hypesquad: badges.append("🔥 HypeSquad")
        if flags.bug_hunter: badges.append("🐛 Bug Hunter")
        if flags.active_developer: badges.append("💻 Active Developer")
        if flags.verified_bot: badges.append("🤖 認証済みBot")
        if flags.early_supporter: badges.append("🎖️ 早期サポーター")
        
        if isinstance(user, discord.Member) and user.premium_since:
            badges.append("💎 サーバーブースター")
        
        return " | ".join(badges) if badges else "一般市民"

    # --- ヘルパー: デバイス特定 ---
    def get_device_status(self, member):
        if not member or member.status == discord.Status.offline:
            return ""
        devices = []
        if member.desktop_status != discord.Status.offline: devices.append("💻 PC")
        if member.mobile_status != discord.Status.offline: devices.append("📱 モバイル")
        if member.web_status != discord.Status.offline: devices.append("🌐 Web")
        return f"({ ' / '.join(devices) })" if devices else ""

    @app_commands.command(name="user", description="対象の公開情報・ステータス・資産状況を精密調査します")
    @app_commands.describe(target="ユーザーID、またはメンション（未入力で自分を調査）")
    async def user_info(self, it: discord.Interaction, target: str = None):
        await it.response.defer()

        user_obj = None
        is_member = False

        # 1. ターゲット解析（自分または指定ユーザーをMemberとして取得）
        if target is None:
            if it.guild:
                user_obj = it.guild.get_member(it.user.id)
            if user_obj:
                is_member = True
            else:
                user_obj = it.user
        else:
            clean_id_match = re.search(r'\d+', target)
            if clean_id_match:
                clean_id = int(clean_id_match.group())
                try:
                    if it.guild:
                        user_obj = it.guild.get_member(clean_id)
                    
                    if user_obj:
                        is_member = True
                    else:
                        user_obj = await self.bot.fetch_user(clean_id)
                except Exception:
                    user_obj = None

        if user_obj is None:
            return await it.followup.send("❌ **ターゲットを捕捉できません。** 有効なIDを入力してください。", ephemeral=True)

        # 2. 経済データ取得
        u_data = {"money": 0, "xp": 0}
        if self.ledger:
            u_data = self.ledger.get_user(user_obj.id)

        # 3. デザイン（ロールカラーの採用）
        accent_color = 0x4C566A
        if is_member and user_obj.color.value != 0:
            accent_color = user_obj.color

        embed = discord.Embed(
            title=f"📋 精密調査報告書: {user_obj.global_name or user_obj.name}",
            color=accent_color,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=user_obj.display_avatar.url)

        # --- Section: 識別情報 ---
        created_ts = int(user_obj.created_at.timestamp())
        identity_val = (
            f"**ID**: `{user_obj.id}`\n"
            f"**作成日**: <t:{created_ts}:D> (<t:{created_ts}:R>)\n"
            f"**バッジ**: {self.get_user_badges(user_obj)}"
        )
        embed.add_field(name="🆔 識別情報", value=identity_val, inline=False)

        # --- Section: ステータス & アクティビティ ---
        if is_member:
            status_map = {
                discord.Status.online: "🟢 オンライン",
                discord.Status.idle: "🌙 退席中",
                discord.Status.dnd: "🔴 取り込み中",
                discord.Status.offline: "⚪ オフライン"
            }
            curr_stat = status_map.get(user_obj.status, "⚪ オフライン")
            device_str = self.get_device_status(user_obj)
            
            # アクティビティ解析（リンク対応）
            activity_list = []
            for act in user_obj.activities:
                if isinstance(act, discord.Spotify):
                    # Spotify楽曲への直接リンク
                    track_url = f"https://open.spotify.com/track/{act.track_id}"
                    activity_list.append(f"🎵 **Spotify**: [{act.title}]({track_url})")
                elif isinstance(act, discord.Game):
                    activity_list.append(f"🎮 **Game**: {act.name}")
                elif isinstance(act, discord.Streaming):
                    activity_list.append(f"📡 **Streaming**: [{act.name}]({act.url})")
                elif isinstance(act, discord.CustomActivity):
                    c_text = (f"{act.emoji} " if act.emoji else "") + (str(act.name) if act.name else "")
                    if c_text: activity_list.append(f"📝 **Status**: {c_text}")

            joined_ts = int(user_obj.joined_at.timestamp())
            presence_val = (
                f"**状態**: {curr_stat} {device_str}\n"
                f"**活動**: {', '.join(activity_list) if activity_list else 'なし'}\n"
                f"**参加日**: <t:{joined_ts}:D> (<t:{joined_ts}:R>)"
            )
            embed.add_field(name="🏠 活動状況", value=presence_val, inline=False)

        # --- Section: 経済データ ---
        sys_val = (
            f"**所持金**: `{u_data.get('money', 0):,} cr`\n"
            f"**経験値**: `{u_data.get('xp', 0):,} xp`"
        )
        embed.add_field(name="💎 資産データ", value=sys_val, inline=True)

        # フッター
        footer_text = "Rb m/25E Operations"
        if user_obj.id == ADMIN_ID:
            footer_text = "⚠️ Rb m/25E 最高管理者"
        embed.set_footer(text=footer_text, icon_url=self.bot.user.display_avatar.url)

        await it.followup.send(embed=embed)

async def setup(bot):
    from __main__ import ledger_instance
    await bot.add_cog(User(bot, ledger_instance))
