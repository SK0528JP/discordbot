import discord
from discord.ext import commands
from discord import app_commands
import os
import sys

class Admin(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger
        # 管理者ロールID（以前の設定を継承）
        self.ADMIN_ROLE_ID = 1453336556961140866

    # 管理者チェック用の内部関数
    async def is_admin(self, it: discord.Interaction):
        if any(role.id == self.ADMIN_ROLE_ID for role in it.user.roles):
            return True
        await it.response.send_message("❌ 拒絶：このコマンドを実行する権限がない。当局に通報した。", ephemeral=True)
        return False

    # --- /admin_grant ---
    @app_commands.command(name="admin_grant", description="【管理者用】特定の同志に特別予算を付与")
    async def admin_grant(self, it: discord.Interaction, target: discord.Member, amount: int):
        if not await self.is_admin(it): return

        u = self.ledger.get_user(target.id)
        u["money"] += amount
        self.ledger.save()
        await it.response.send_message(f"📢 告示：同志 {target.display_name} に特別予算 {amount} 資金が承認された。")

    # --- /admin_confiscate ---
    @app_commands.command(name="admin_confiscate", description="【管理者用】不当利得の没収")
    async def admin_confiscate(self, it: discord.Interaction, target: discord.Member, amount: int):
        if not await self.is_admin(it): return

        u = self.ledger.get_user(target.id)
        u["money"] = max(0, u["money"] - amount)
        self.ledger.save()
        await it.response.send_message(f"📢 告示：同志 {target.display_name} の資産より {amount} 資金を国庫へ回収した。")

    # --- /restart ---
    @app_commands.command(name="restart", description="【管理者用】システムの戦略的再起動")
    async def restart(self, it: discord.Interaction):
        if not await self.is_admin(it): return
        
        await it.response.send_message("🔄 了解。システムを一時停止し、次期サイクルでの復帰に備える。")
        # プロセスを終了させる。GitHub Actionsのtimeout-minutesまたは次回のcronで再起動される。
        sys.exit()

async def setup(bot):
    pass
