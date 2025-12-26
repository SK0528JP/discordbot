import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

class Utility(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="ping", description="システムの接続状況を確認します。")
    async def ping(self, it: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="System Status",
            description="ネットワーク接続は良好です。",
            color=0x88a096 # セージグリーン
        )
        embed.add_field(name="Latency", value=f"`{latency}ms`", inline=True)
        embed.add_field(name="Stability", value="Healthy", inline=True)
        embed.set_footer(text="Network Infrastructure Unit")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="status", description="自身のユーザー情報を表示します。")
    async def status(self, it: discord.Interaction):
        u = self.ledger.get_user(it.user.id)
        embed = discord.Embed(title="User Profile", color=0x94a3b8) # スレートブルー
        embed.set_thumbnail(url=it.user.display_avatar.url)
        
        # 情報をシンプルに整列
        embed.add_field(name="Account", value=it.user.display_name, inline=True)
        embed.add_field(name="Credit", value=f"{u['money']:,} 資金", inline=True)
        embed.add_field(name="Experience", value=f"{u['xp']:,} XP", inline=True)
        
        embed.set_footer(text=f"Last Active: {u.get('last_active', 'N/A')}")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="user", description="指定したユーザーの情報を照会します。")
    async def user_info(self, it: discord.Interaction, target: Optional[discord.Member] = None):
        t = target if isinstance(target, discord.Member) else it.user
        u = self.ledger.get_user(t.id)
        
        embed = discord.Embed(title="Member Information", color=0x475569) # スレートグレー
        embed.set_thumbnail(url=t.display_avatar.url)
        
        embed.add_field(name="Display Name", value=t.display_name, inline=True)
        embed.add_field(name="Total XP", value=f"{u['xp']:,}", inline=True)
        embed.add_field(name="Asset Balance", value=f"{u['money']:,}", inline=True)
        
        embed.set_footer(text="Registry Search Result")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="help", description="操作ガイドを表示します。")
    async def help_command(self, it: discord.Interaction):
        embed = discord.Embed(
            title="System Guide",
            description="各セクションで利用可能な機能の一覧です。",
            color=0x2c3e50
        )
        embed.add_field(name="Utility", value="`/status` `/user` `/ping`", inline=False)
        embed.add_field(name="Economy", value="`/pay` `/exchange` `/ranking` `/money_ranking`", inline=False)
        embed.add_field(name="Communication", value="`/janken` `/omikuji` `/meigen` `/roulette` `/comment`", inline=False)
        embed.add_field(name="Admin", value="`/admin_grant` `/admin_confiscate` `/restart`", inline=False)
        
        embed.set_footer(text="Support Documentation")
        await it.response.send_message(embed=embed, ephemeral=True)
