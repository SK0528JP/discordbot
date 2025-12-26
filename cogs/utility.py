import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

class Utility(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="ping", description="システムの応答速度および接続状況を確認します。")
    async def ping(self, it: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="システムステータス報告",
            description="現在のネットワーク接続状況は正常です。",
            color=0x27ae60 # 正常を示す緑
        )
        embed.add_field(name="レイテンシ", value=f"`{latency}ms`", inline=True)
        embed.add_field(name="稼働状況", value="✅ Online", inline=True)
        embed.set_footer(text="Network Infrastructure Unit")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="status", description="自身のユーザープロファイルおよび資産状況を表示します。")
    async def status(self, it: discord.Interaction):
        u = self.ledger.get_user(it.user.id)
        embed = discord.Embed(title="ユーザープロファイル照会", color=0x34495e)
        embed.set_thumbnail(url=it.user.display_avatar.url)
        
        # 統計データをコードブロックで整理
        stats = (
            f"貢献度 (XP) : {u['xp']:,}\n"
            f"保有資産    : {u['money']:,} 資金\n"
            f"登録日      : {u.get('joined_at', 'N/A')}"
        )
        embed.description = f"```\n{stats}\n```"
        embed.set_footer(text=f"User ID: {it.user.id}")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="user", description="指定したユーザーの公開情報を照会します。")
    async def user_info(self, it: discord.Interaction, target: Optional[discord.Member] = None):
        t = target if isinstance(target, discord.Member) else it.user
        u = self.ledger.get_user(t.id)
        
        embed = discord.Embed(title="対象ユーザー情報", color=0x7f8c8d)
        embed.set_thumbnail(url=t.display_avatar.url)
        
        info = (
            f"アカウント : {t.display_name}\n"
            f"累計XP     : {u['xp']:,}\n"
            f"資産総額   : {u['money']:,}\n"
            f"最終アクティブ : {u['last_active']}"
        )
        embed.description = f"```\n{info}\n```"
        embed.set_footer(text="Internal Database Registry")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="help", description="利用可能なコマンドの一覧を表示します。")
    async def help_command(self, it: discord.Interaction):
        embed = discord.Embed(
            title="システム操作マニュアル",
            description="各モジュールで利用可能なスラッシュコマンドの一覧です。",
            color=0x2c3e50
        )
        embed.add_field(name="📊 情報参照 (Utility)", value="`/status` `/user` `/ping`", inline=False)
        embed.add_field(name="💰 資産管理 (Economy)", value="`/pay` `/exchange` `/ranking` `/money_ranking`", inline=False)
        embed.add_field(name="🎲 支援機能 (Entertainment)", value="`/janken` `/omikuji` `/meigen` `/roulette` `/comment`", inline=False)
        embed.add_field(name="🛠️ 管理権限 (Admin)", value="`/admin_grant` `/admin_confiscate` `/restart`", inline=False)
        
        embed.set_footer(text="System Documentation")
        await it.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    pass
