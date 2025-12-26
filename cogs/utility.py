import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

class Utility(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="ping", description="通信インフラの健全性を確認")
    async def ping(self, it: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="📡 通信インフラ状況報告",
            description=f"現在の応答速度は極めて良好である。",
            color=0x00ff00 # 緑
        )
        embed.add_field(name="レイテンシ", value=f"**{latency}ms**", inline=True)
        embed.add_field(name="接続状態", value="✅ 正常稼働中", inline=True)
        embed.set_footer(text="国家通信局 🛰️")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="status", description="自身の労働手帳を確認")
    async def status(self, it: discord.Interaction):
        u = self.ledger.get_user(it.user.id)
        embed = discord.Embed(title=f"📋 {it.user.display_name} の労働手帳", color=0xff0000)
        embed.set_thumbnail(url=it.user.display_avatar.url)
        embed.add_field(name="貢献度 (XP)", value=f"**{u['xp']}** XP", inline=True)
        embed.add_field(name="所持金", value=f"**{u['money']}** 資金", inline=True)
        embed.add_field(name="入隊日", value=f"{u.get('joined_at', '不明')}", inline=False)
        await it.response.send_message(embed=embed)

    @app_commands.command(name="user", description="同志の記録を照会")
    async def user_info(self, it: discord.Interaction, target: Optional[discord.Member] = None):
        t = target if isinstance(target, discord.Member) else it.user
        u = self.ledger.get_user(t.id)
        
        embed = discord.Embed(title=f"🎖️ 同志 {t.display_name} の個人記録", color=0xcc0000)
        embed.set_thumbnail(url=t.display_avatar.url)
        embed.add_field(name="貢献度", value=f"**{u['xp']}** XP", inline=True)
        embed.add_field(name="資産", value=f"**{u['money']}** 資金", inline=True)
        embed.set_footer(text=f"最終活動：{u['last_active']}")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="help", description="国家マニュアルを表示")
    async def help_command(self, it: discord.Interaction):
        embed = discord.Embed(
            title="📜 国家管理システム運用マニュアル",
            description="諸君の労働を支援する全機能のリストである。",
            color=0x333333
        )
        embed.add_field(name="📊 情報", value="`/status` `/user` `/ping`", inline=False)
        embed.add_field(name="💰 経済", value="`/pay` `/exchange` `/ranking` `/money_ranking`", inline=False)
        embed.add_field(name="🎲 娯楽", value="`/janken` `/omikuji` `/meigen` `/roulette` `/comment`", inline=False)
        embed.add_field(name="🛠️ 管理", value="`/admin_grant` `/admin_confiscate` `/restart`", inline=False)
        await it.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    pass # main.py側でロードされるため空でOK
