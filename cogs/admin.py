import discord
from discord.ext import commands
from discord import app_commands
import sys
from strings import STRINGS

class Admin(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger
        # 管理権限設定（あなたのIDをここにセットしてください）
        self.ADMIN_USER_IDS = [840821281838202880]

    async def is_admin(self, it: discord.Interaction, lang: str):
        """権限照会プロセス"""
        if it.user.id in self.ADMIN_USER_IDS:
            return True
            
        # 権限がない場合のフィードバック
        s = STRINGS.get(lang, STRINGS["en"])
        embed = discord.Embed(
            title="Access Denied",
            description=s["access_denied"],
            color=0xe74c3c 
        )
        await it.response.send_message(embed=embed, ephemeral=True)
        return False

    @app_commands.command(name="admin_grant", description="Grant assets to a user / 資金付与 / Ge tillgångar")
    @app_commands.describe(target="Target user", amount="Amount")
    async def admin_grant(self, it: discord.Interaction, target: discord.Member, amount: int):
        u_admin = self.ledger.get_user(it.user.id)
        lang = u_admin.get("lang", "ja")
        
        if not await self.is_admin(it, lang): return
        
        u_target = self.ledger.get_user(target.id)
        u_target["money"] += amount
        self.ledger.save()
        
        s = STRINGS.get(lang, STRINGS["ja"])
        embed = discord.Embed(title="Asset Allocation Authorized", color=0x94a3b8)
        embed.add_field(name="Target", value=target.display_name, inline=True)
        embed.add_field(name="Amount", value=f"```fix\n+ {amount:,}\n```", inline=False)
        embed.set_footer(text=s["footer_admin"])
        
        await it.response.send_message(embed=embed)

    @app_commands.command(name="admin_confiscate", description="Confiscate assets / 資金回収 / Konfiskera")
    async def admin_confiscate(self, it: discord.Interaction, target: discord.Member, amount: int):
        u_admin = self.ledger.get_user(it.user.id)
        lang = u_admin.get("lang", "ja")
        
        if not await self.is_admin(it, lang): return
        
        u_target = self.ledger.get_user(target.id)
        u_target["money"] = max(0, u_target["money"] - amount)
        self.ledger.save()
        
        s = STRINGS.get(lang, STRINGS["ja"])
        embed = discord.Embed(title="Asset Adjustment Applied", color=0x475569)
        embed.add_field(name="Target", value=target.display_name, inline=True)
        embed.add_field(name="Amount", value=f"```diff\n- {amount:,}\n```", inline=False)
        embed.set_footer(text=s["footer_admin"])
        
        await it.response.send_message(embed=embed)

    @app_commands.command(name="restart", description="System reboot / システム再起動 / Starta om systemet")
    async def restart(self, it: discord.Interaction):
        u_admin = self.ledger.get_user(it.user.id)
        lang = u_admin.get("lang", "ja")
        
        if not await self.is_admin(it, lang): return
        
        s = STRINGS.get(lang, STRINGS["ja"])
        embed = discord.Embed(title="System Maintenance: Reboot", color=0x1e293b)
        embed.description = "Initializing shutdown..."
        embed.set_footer(text=s["footer_admin"])
        
        await it.response.send_message(embed=embed)
        print(f"[SYSTEM] REBOOT AUTHORIZED BY {it.user.name}")
        
        # GitHub Actions環境ではプロセス終了により再起動を試みる
        sys.exit()

async def setup(bot):
    from __main__ import ledger_instance
    await bot.add_cog(Admin(bot, ledger_instance))
