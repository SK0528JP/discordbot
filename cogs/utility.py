import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import datetime

class Utility(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    # --- /ping ---
    @app_commands.command(name="ping", description="通信インフラの健全性を確認")
    async def ping(self, it: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await it.response.send_message(f"📡 報告：通信遅延は {latency}ms である。良好だ！")

    # --- /status ---
    @app_commands.command(name="status", description="自身の労働手帳を確認")
    async def status(self, it: discord.Interaction):
        u = self.ledger.get_user(it.user.id)
        embed = discord.Embed(title=f"📋 {it.user.display_name} の労働手帳", color=0xff0000)
        embed.add_field(name="貢献度 (XP)", value=f"{u['xp']} XP", inline=True)
        embed.add_field(name="所持金", value=f"{u['money']} 資金", inline=True)
        await it.response.send_message(embed=embed)

    # --- /user ---
    @app_commands.command(name="user", description="同志の記録を照会")
    async def user_info(self, it: discord.Interaction, target: Optional[discord.Member] = None):
        # 変換エラー対策：targetが正しく取得できない場合は実行者本人にする
        t = target if isinstance(target, discord.Member) else it.user
        u = self.ledger.get_user(t.id)
        
        embed = discord.Embed(title=f"🎖️ 同志 {t.display_name} の記録", color=0xcc0000)
        embed.set_thumbnail(url=t.display_avatar.url)
        embed.add_field(name="貢献度", value=f"{u['xp']} XP", inline=True)
        embed.add_field(name="資産", value=f"{u['money']} 資金", inline=True)
        embed.set_footer(text=f"最終活動：{u['last_active']}")
        await it.response.send_message(embed=embed)

    # --- /help ---
    @app_commands.command(name="help", description="国家マニュアルを表示")
    async def help_command(self, it: discord.Interaction):
        embed = discord.Embed(title="📜 国家管理システム運用マニュアル", color=0x333333)
        embed.add_field(name="基本", value="`/status` `/user` `/ping`", inline=False)
        embed.add_field(name="経済", value="`/pay` `/exchange` `/ranking`", inline=False)
        embed.add_field(name="娯楽", value="`/janken` `/omikuji` `/meigen`", inline=False)
        await it.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    # main.py側で初期化したledgerインスタンスを受け取る仕組みにする
    # 実際の追加処理はmain.py側で後ほど記述
    pass
