import discord
from discord.ext import commands
from discord import app_commands
import sys

class Admin(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger
        # 権限設定
        self.ADMIN_ROLE_ID = 1453336556961140866
        self.ADMIN_USER_IDS = [840821281838202880] # 特権管理者リスト

    async def is_admin(self, it: discord.Interaction):
        # 権限照会
        has_role = any(role.id == self.ADMIN_ROLE_ID for role in it.user.roles)
        is_special_user = it.user.id in self.ADMIN_USER_IDS
        
        if has_role or is_special_user:
            return True
            
        await it.response.send_message("アクセス権限がありません。管理者にお問い合わせください。", ephemeral=True)
        return False

    @app_commands.command(name="admin_grant", description="指定ユーザーに資金を付与します。")
    async def admin_grant(self, it: discord.Interaction, target: discord.Member, amount: int):
        if not await self.is_admin(it): return
        
        u = self.ledger.get_user(target.id)
        u["money"] += amount
        self.ledger.save()
        
        embed = discord.Embed(title="資金付与完了", color=0x2ecc71) # 正常終了の緑
        embed.description = f"{target.mention} 様への **{amount} 資金** の付与処理が完了いたしました。"
        embed.set_footer(text="Financial Management System")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="admin_confiscate", description="指定ユーザーから資金を回収します。")
    async def admin_confiscate(self, it: discord.Interaction, target: discord.Member, amount: int):
        if not await self.is_admin(it): return
        
        u = self.ledger.get_user(target.id)
        u["money"] = max(0, u["money"] - amount)
        self.ledger.save()
        
        embed = discord.Embed(title="資金回収完了", color=0xe67e22) # 警告・変動のオレンジ
        embed.description = f"{target.mention} 様の口座より **{amount} 資金** を回収いたしました。"
        embed.set_footer(text="Audit & Compliance Department")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="restart", description="システムを安全に再起動します。")
    async def restart(self, it: discord.Interaction):
        if not await self.is_admin(it): return
        
        embed = discord.Embed(
            title="システム再起動の通知", 
            description="サーバーの最適化および更新適用のための再起動プロセスを開始します。\nしばらくお待ちください。", 
            color=0x34495e # 落ち着いたネイビー
        )
        embed.add_field(name="実行担当者", value=it.user.name, inline=True)
        embed.add_field(name="状況", value="🔄 終了処理中", inline=True)
        embed.set_footer(text="System Infrastructure Unit")
        
        await it.response.send_message(embed=embed)
        
        print(f"[SYSTEM] Restart initiated by {it.user.name}({it.user.id}).")
        sys.exit()

async def setup(bot):
    pass
