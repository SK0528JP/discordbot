import discord
from discord.ext import commands
from discord import app_commands
import sys

class Admin(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger
        # 管理権限を持つユーザーID（あなたのIDに変更してください）
        self.ADMIN_USER_IDS = [840821281838202880]

    async def is_admin(self, it: discord.Interaction):
        """権限があるか確認し、ない場合は通知します。"""
        if it.user.id in self.ADMIN_USER_IDS:
            return True
            
        embed = discord.Embed(
            title="アクセス拒否",
            description="このコマンドを実行する権限がありません。",
            color=0xe74c3c 
        )
        await it.response.send_message(embed=embed, ephemeral=True)
        return False

    @app_commands.command(name="admin_grant", description="指定したユーザーに資産を付与します")
    @app_commands.describe(target="付与対象のユーザー", amount="付与する金額")
    async def admin_grant(self, it: discord.Interaction, target: discord.Member, amount: int):
        if not await self.is_admin(it): return
        
        u_target = self.ledger.get_user(target.id)
        u_target["money"] += amount
        self.ledger.save()
        
        embed = discord.Embed(title="資産付与完了", color=0x94a3b8)
        embed.add_field(name="対象者", value=target.display_name, inline=True)
        embed.add_field(name="付与額", value=f"```fix\n+ {amount:,} cr\n```", inline=False)
        embed.set_footer(text="Rb m/25 行政プロトコル")
        
        await it.response.send_message(embed=embed)

    @app_commands.command(name="admin_confiscate", description="指定したユーザーから資産を回収します")
    @app_commands.describe(target="回収対象のユーザー", amount="回収する金額")
    async def admin_confiscate(self, it: discord.Interaction, target: discord.Member, amount: int):
        if not await self.is_admin(it): return
        
        u_target = self.ledger.get_user(target.id)
        u_target["money"] = max(0, u_target["money"] - amount)
        self.ledger.save()
        
        embed = discord.Embed(title="資産回収完了", color=0x475569)
        embed.add_field(name="対象者", value=target.display_name, inline=True)
        embed.add_field(name="回収額", value=f"```diff\n- {amount:,} cr\n```", inline=False)
        embed.set_footer(text="Rb m/25 行政プロトコル")
        
        await it.response.send_message(embed=embed)

    @app_commands.command(name="restart", description="システムを再起動（終了）します")
    async def restart(self, it: discord.Interaction):
        if not await self.is_admin(it): return
        
        embed = discord.Embed(title="システムメンテナンス", description="シャットダウンを開始します...", color=0x1e293b)
        embed.set_footer(text="Rb m/25 行政プロトコル")
        
        await it.response.send_message(embed=embed)
        print(f"[SYSTEM] 再起動が実行されました: 実行者 {it.user.name}")
        
        # プロセスを終了させることでGitHub Actionsの再起動を促す
        sys.exit()

async def setup(bot):
    from __main__ import ledger_instance
    await bot.add_cog(Admin(bot, ledger_instance))
