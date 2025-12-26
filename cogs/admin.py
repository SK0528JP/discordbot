import discord
from discord.ext import commands
from discord import app_commands
import sys

class Admin(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger
        # 管理者設定
        self.ADMIN_ROLE_ID = 1453336556961140866
        self.ADMIN_USER_IDS = [840821281838202880]  # 特権ユーザーリスト

    async def is_admin(self, it: discord.Interaction):
        # ロール保有確認、または指定ユーザーIDであるかを確認
        has_role = any(role.id == self.ADMIN_ROLE_ID for role in it.user.roles)
        is_special_user = it.user.id in self.ADMIN_USER_IDS
        
        if has_role or is_special_user:
            return True
            
        await it.response.send_message("❌ 拒絶：貴殿にはこの指令を実行する権限が付与されていない。アクセス試行を記録した。", ephemeral=True)
        return False

    @app_commands.command(name="admin_grant", description="【管理者用】特別予算を付与")
    async def admin_grant(self, it: discord.Interaction, target: discord.Member, amount: int):
        if not await self.is_admin(it): return
        u = self.ledger.get_user(target.id)
        u["money"] += amount
        self.ledger.save()
        
        embed = discord.Embed(title="📢 国家予算承認", color=0xffd700)
        embed.description = f"中央審議会の決定に基づき、同志 {target.mention} へ **{amount} 資金** の特別予算を付与した。"
        embed.set_footer(text="国家財務局 🏛️")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="admin_confiscate", description="【管理者用】資産の回収")
    async def admin_confiscate(self, it: discord.Interaction, target: discord.Member, amount: int):
        if not await self.is_admin(it): return
        u = self.ledger.get_user(target.id)
        u["money"] = max(0, u["money"] - amount)
        self.ledger.save()
        
        embed = discord.Embed(title="📢 資産没収宣告", color=0xff0000)
        embed.description = f"中央監察局の命令により、同志 {target.mention} の資産より **{amount} 資金** を国庫へ強制回収した。"
        embed.set_footer(text="国家中央監察局 ⚖️")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="restart", description="【管理者用】システム統括再起動")
    async def restart(self, it: discord.Interaction):
        if not await self.is_admin(it): return
        
        embed = discord.Embed(
            title="🔄 システム戦略的再起動の執行", 
            description="当機はこれより、システムの整合性維持および最適化を目的とした戦略的再起動プロセスに移行する。\n\n**「国家の安定は、不断の刷新によって保たれる。」**", 
            color=0x2c3e50
        )
        embed.add_field(name="執行者", value=it.user.mention, inline=True)
        embed.add_field(name="ステータス", value="🔄 プロセス開始...", inline=True)
        embed.set_footer(text="中央情報処理部 🛰️")
        
        await it.response.send_message(embed=embed)
        
        # ログに記録してから終了
        print(f"[RESTART] {it.user.name}({it.user.id}) により再起動が執行されました。")
        sys.exit()

async def setup(bot):
    pass
