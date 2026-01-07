import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta, timezone
import json
import os
import asyncio

# データ保存用ファイル
DATA_FILE = "invite_logs.json"

class InviteSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invite_cache = {}  # {guild_id: {code: uses}}
        self.db = self.load_data()

    # --- データ管理 (JSON) ---
    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return {}
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.db, f, indent=4)

    # --- 招待キャッシュ管理 ---
    async def cache_guild_invites(self, guild):
        """特定のギルドの招待キャッシュを更新"""
        try:
            # サーバー管理権限がないと取得できないためtry-except
            invites = await guild.invites()
            self.invite_cache[guild.id] = {inv.code: inv.uses for inv in invites}
        except discord.Forbidden:
            print(f"⚠️ 権限不足: サーバー({guild.name})の招待リンクを取得できません。")
        except Exception as e:
            print(f"Error caching invites for {guild.name}: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        """起動時に全サーバーのキャッシュを構築"""
        for guild in self.bot.guilds:
            await self.cache_guild_invites(guild)
        print("✅ Invite Tracker is ready.")

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        """招待が作成されたらキャッシュ更新"""
        await self.cache_guild_invites(invite.guild)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        """招待が削除されたらキャッシュ更新"""
        await self.cache_guild_invites(invite.guild)

    # --- 参加検知 & 記録ロジック ---
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        if guild.id not in self.invite_cache:
            await self.cache_guild_invites(guild)
            return

        old_invites = self.invite_cache[guild.id]
        used_invite = None
        
        try:
            new_invites = await guild.invites()
            
            # 使用回数が増えたリンクを探す
            for inv in new_invites:
                if inv.uses > old_invites.get(inv.code, 0):
                    used_invite = inv
                    break
            
            # キャッシュを最新に更新
            self.invite_cache[guild.id] = {inv.code: inv.uses for inv in new_invites}

            # データベースに記録
            if used_invite:
                gid_str = str(guild.id)
                uid_str = str(member.id)
                
                if gid_str not in self.db:
                    self.db[gid_str] = {}

                self.db[gid_str][uid_str] = {
                    "code": used_invite.code,
                    "inviter_id": used_invite.inviter.id if used_invite.inviter else None,
                    "uses": used_invite.uses,
                    "joined_at": datetime.now().timestamp()
                }
                self.save_data()
                print(f"🔍 Tracked: {member.name} joined via {used_invite.code}")

        except discord.Forbidden:
            pass

    # --- 調査コマンド ---
    @app_commands.command(name="invite_search", description="ユーザーの招待経路（参加に使用したリンク）を調査します")
    @app_commands.describe(
        target="調査対象のユーザー",
        mode="結果の表示モード（デフォルト: 自分のみ）"
    )
    @app_commands.choices(mode=[
        app_commands.Choice(name="🔒 自分のみ表示 (Private)", value=1),
        app_commands.Choice(name="📢 公開して表示 (Public)", value=0)
    ])
    async def invite_search(self, it: discord.Interaction, target: discord.Member, mode: app_commands.Choice[int] = None):
        is_ephemeral = True
        if mode and mode.value == 0:
            is_ephemeral = False
        
        await it.response.defer(ephemeral=is_ephemeral)

        # DBからデータ検索
        gid_str = str(it.guild.id)
        uid_str = str(target.id)
        
        record = self.db.get(gid_str, {}).get(uid_str)
        
        # JST設定
        JST = timezone(timedelta(hours=9), 'JST')
        now_jst = datetime.now(JST)

        embed = discord.Embed(
            title=f"🔍 招待経路調査: {target.display_name}",
            color=0x88C0D0,
            timestamp=now_jst
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        if record:
            inviter_id = record.get("inviter_id")
            inviter_mention = f"<@{inviter_id}>" if inviter_id else "不明/削除済み"
            code = record.get("code")
            uses = record.get("uses")
            joined_ts = int(record.get("joined_at"))

            val = (
                f"**使用コード**: `{code}`\n"
                f"**招待作成者**: {inviter_mention} (`{inviter_id}`)\n"
                f"**参加日時**: <t:{joined_ts}:f>\n"
                f"**リンク使用回数**: {uses}回 (参加時点)"
            )
            embed.add_field(name="✅ 追跡成功", value=val, inline=False)
        else:
            # 記録がない場合
            val = (
                "⚠️ **記録が見つかりません**\n"
                "以下の可能性があります：\n"
                "・Bot導入前に参加した\n"
                "・特殊な招待（バニティURLやウィジェット）を使用した\n"
                "・Botに「サーバー管理」権限がない"
            )
            embed.add_field(name="❌ 追跡不能", value=val, inline=False)

        # フッター
        embed.set_footer(text=f"Rb m/25E 追跡モジュール | {now_jst.strftime('%Y-%m-%d %H:%M:%S')}")

        await it.followup.send(embed=embed, ephemeral=is_ephemeral)

async def setup(bot):
    await bot.add_cog(InviteSearch(bot))
