import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

class User(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    # --- ヘルパー関数: バッジ（フラグ）の解析 ---
    def get_user_badges(self, user):
        badges = []
        flags = user.public_flags
        
        if flags.staff: badges.append("Discord Staff")
        if flags.partner: badges.append("Partner")
        if flags.hypesquad: badges.append("HypeSquad")
        if flags.bug_hunter: badges.append("Bug Hunter")
        if flags.active_developer: badges.append("Active Dev")
        if flags.verified_bot: badges.append("Verified Bot")
        if flags.early_supporter: badges.append("Early Supporter")
        
        return ", ".join(badges) if badges else "No Special Badges"

    # --- ヘルパー関数: 接続デバイスの特定 ---
    def get_device_status(self, member):
        if str(member.status) == "offline":
            return ""
        
        devices = []
        if member.desktop_status != discord.Status.offline: devices.append("💻 PC")
        if member.mobile_status != discord.Status.offline: devices.append("📱 Mobile")
        if member.web_status != discord.Status.offline: devices.append("🌐 Web")
        
        return " / ".join(devices) if devices else "Unknown Device"

    # --- コマンド本体 ---
    @app_commands.command(name="user", description="対象の公開情報・ステータス・資産状況を精密調査します")
    @app_commands.describe(target="ユーザーID、またはメンション（未入力で自分を調査）")
    async def user_info(self, it: discord.Interaction, target: str = None):
        await it.response.defer()

        # 1. ターゲットの特定とオブジェクト取得
        user_obj = None
        is_member = False # サーバーメンバーかどうかのフラグ

        if target is None:
            user_obj = it.user
            is_member = True
        else:
            # IDのクリーニング (<@1234...> -> 1234...)
            clean_id = target.replace("<@", "").replace(">", "").replace("!", "").replace("&", "")
            
            if clean_id.isdigit():
                try:
                    # まずサーバー内メンバーとして検索（アクティビティ取得のため重要）
                    if it.guild:
                        user_obj = it.guild.get_member(int(clean_id))
                    
                    if user_obj:
                        is_member = True
                    else:
                        # サーバーにいない場合はAPIから基本情報だけ取得
                        user_obj = await self.bot.fetch_user(int(clean_id))
                except Exception:
                    user_obj = None

        # 特定失敗時の処理
        if user_obj is None:
            embed_error = discord.Embed(
                description="❌ **Target Lost.**\n有効なユーザーIDまたはメンションを指定してください。",
                color=0xFF5555
            )
            await it.followup.send(embed=embed_error, ephemeral=True)
            return

        # 2. 経済データの取得 (Ledger)
        # データがない場合はデフォルト値 (0) を使用してエラー回避
        u_data = {"money": 0, "xp": 0, "joined_at": "Unregistered"}
        if self.ledger:
            try:
                raw_data = self.ledger.get_user(user_obj.id)
                if raw_data:
                    u_data = raw_data
            except Exception:
                pass # 取得失敗時も処理を続行

        # 3. Embedデザインの構築
        # 北欧デザイン: オフラインや一般ユーザーは落ち着いたスレートグレー(0x4C566A)
        # メンバーかつ色設定がある場合のみ、その色を使用
        accent_color = 0x4C566A
        if is_member and user_obj.color.value != 0:
            accent_color = user_obj.color

        embed = discord.Embed(
            title=f"Investigation Report: {user_obj.name}",
            color=accent_color,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=user_obj.display_avatar.url)

        # --- Section A: Identity (基本識別情報) ---
        created_ts = int(user_obj.created_at.timestamp())
        badge_str = self.get_user_badges(user_obj)
        
        identity_val = (
            f"**UID**: `{user_obj.id}`\n"
            f"**Type**: {'🤖 Bot' if user_obj.bot else '👤 User'}\n"
            f"**Created**: <t:{created_ts}:D> (<t:{created_ts}:R>)\n"
            f"**Badges**: {badge_str}"
        )
        embed.add_field(name="🆔 Identity", value=identity_val, inline=False)

        # --- Section B: Server Presence (サーバー内情報) ---
        # メンバーである場合のみ表示（fetch_userでは取得不可能）
        if is_member:
            # 参加日
            joined_ts = int(user_obj.joined_at.timestamp())
            
            # ロール (Everyoneを除外、上位6つを表示)
            roles = [r.mention for r in reversed(user_obj.roles) if r.name != "@everyone"]
            role_str = " ".join(roles[:6])
            if len(roles) > 6: role_str += "..."
            
            # 重要権限のチェック
            key_perms = []
            p = user_obj.guild_permissions
            if p.administrator: key_perms.append("⚡ Administrator")
            elif p.manage_guild: key_perms.append("🛡️ Manager")
            if p.ban_members: key_perms.append("🚫 Ban Hammer")
            perm_str = ", ".join(key_perms) if key_perms else "Standard"

            presence_val = (
                f"**Joined**: <t:{joined_ts}:D> (<t:{joined_ts}:R>)\n"
                f"**Roles**: {role_str if role_str else 'None'}\n"
                f"**Clearance**: {perm_str}"
            )
            embed.add_field(name="🏠 Server Status", value=presence_val, inline=False)

            # --- Section C: Real-time Activity (現在のアクティビティ) ---
            # ここがSpotify修正の肝。複数のアクティビティをすべて解析する。
            
            # ステータス表示
            status_map = {
                discord.Status.online: "🟢 Online",
                discord.Status.idle: "🌙 Idle",
                discord.Status.dnd: "🔴 DND",
                discord.Status.offline: "⚪ Offline",
                discord.Status.invisible: "⚪ Offline"
            }
            curr_stat = status_map.get(user_obj.status, "Unknown")
            device_str = self.get_device_status(user_obj)
            
            activity_list = []
            
            # アクティビティ解析ループ
            if user_obj.activities:
                for act in user_obj.activities:
                    # 1. Spotify (最優先)
                    if isinstance(act, discord.Spotify):
                        # リンクを作成してUX向上
                        track_link = f"[{act.title}](https://open.spotify.com/track/{act.track_id})"
                        activity_list.append(f"🎵 **Spotify**: {track_link} by {act.artist}")
                    
                    # 2. Game
                    elif isinstance(act, discord.Game):
                        start_info = ""
                        if act.start:
                            start_info = f" (<t:{int(act.start.timestamp())}:R>)"
                        activity_list.append(f"🎮 **Game**: {act.name}{start_info}")
                    
                    # 3. Streaming
                    elif isinstance(act, discord.Streaming):
                        activity_list.append(f"📡 **Live**: [{act.name}]({act.url})")
                    
                    # 4. Custom Status
                    elif isinstance(act, discord.CustomActivity):
                        c_text = ""
                        if act.emoji: c_text += str(act.emoji) + " "
                        if act.name: c_text += act.name
                        if c_text:
                            activity_list.append(f"📝 **Status**: {c_text}")
            
            # アクティビティ情報の結合
            act_content = f"**Condition**: {curr_stat} {device_str}\n"
            if activity_list:
                act_content += "\n".join(activity_list)
            else:
                act_content += "No active signal."

            embed.add_field(name="🚀 Live Activity", value=act_content, inline=False)

        # --- Section D: Rb m/25 Economy (経済データ) ---
        sys_val = (
            f"**Assets**: `{u_data.get('money', 0):,} cr`\n"
            f"**Exp**: `{u_data.get('xp', 0):,} xp`"
        )
        embed.add_field(name="💎 System Data", value=sys_val, inline=True)

        # フッター
        ft_text = f"Rb m/25 Tactical System | AID: {user_obj.id}"
        if user_obj.id == 840821281838202880: # 管理者ID
             ft_text = "⚠️ Rb m/25 System Admin | " + ft_text
        
        embed.set_footer(text=ft_text)

        await it.followup.send(embed=embed)

async def setup(bot):
    # main.py の global変数からLedgerインスタンスを安全にインポート
    from __main__ import ledger_instance
    await bot.add_cog(User(bot, ledger_instance))
