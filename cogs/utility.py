import discord
from discord.ext import commands
from discord import app_commands

class Utility(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="help", description="Rb m/25 の操作ガイドを表示します")
    async def help_command(self, it: discord.Interaction):
        """
        システムの使いかたを解説するヘルプコマンド
        """
        embed = discord.Embed(
            title="🌿 Rb m/25 システムガイド",
            description=(
                "Rb m/25 は、北欧モダニズムの思想を取り入れた多機能管理システムです。\n\n"
                "### 💎 資産と貢献度\n"
                "- **貢献度 (XP)**: チャットで発言するたびに蓄積されます。\n"
                "- **資産 (Credits)**: ゲームや送金で使用する通貨です。\n\n"
                "### 📜 主要コマンド\n"
                "- `/status` : 自分の現在の資産とXPをクイック確認します。\n"
                "- `/user` : 自分や他人の詳細なプロファイルを表示します。\n"
                "- `/ranking` : サーバー内の長者・貢献者ランキングを表示します。\n"
                "- `/pay` : 他のユーザーに資産を送金します。\n"
                "- `/janken` : じゃんけんで遊びます（勝利で報酬あり）。\n"
                "- `/fortune` : 今日のおみくじを引きます。\n"
                "- `/ping` : 応答速度を測定します。"
            ),
            color=0x475569
        )
        embed.set_author(name="Rb m/25 インターフェース", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Rb m/25 Infrastructure Division")
        
        await it.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="status", description="自分の簡易ステータスを表示します")
    async def status(self, it: discord.Interaction):
        """
        自分の現在の数値を表示
        """
        u = self.ledger.get_user(it.user.id)
        
        embed = discord.Embed(color=0xf8fafc)
        embed.set_author(name=f"{it.user.display_name} のステータス", icon_url=it.user.display_avatar.url)
        
        status_info = (
            f"💰 **保有資産**: {u.get('money', 0):,} cr\n"
            f"✨ **貢献度**: {u.get('xp', 0):,} XP"
        )
        embed.add_field(name="データ照会", value=status_info, inline=False)
        embed.set_footer(text="Rb m/25 Quick Status")
        
        await it.response.send_message(embed=embed)

    @app_commands.command(name="user", description="指定したユーザーのプロファイルを表示します")
    @app_commands.describe(target="情報を表示したいユーザー")
    async def user_info(self, it: discord.Interaction, target: discord.Member = None):
        """
        指定したユーザー、または自分の詳細情報を表示
        """
        # ターゲット未指定なら自分
        target = target or it.user
        u = self.ledger.get_user(target.id)
        
        embed = discord.Embed(title=f"👤 ユーザープロファイル", color=0x94a3b8)
        embed.set_thumbnail(url=target.display_avatar.url)
        
        # 基本情報
        info = (
            f"**表示名**: {target.display_name}\n"
            f"**ユーザーID**: `{target.id}`\n"
            f"**サーバー参加日**: {target.joined_at.strftime('%Y-%m-%d') if target.joined_at else '不明'}"
        )
        embed.add_field(name="基本データ", value=info, inline=False)
        
        # システムデータ
        stats = (
            f"💰 **保有資産**: {u.get('money', 0):,} cr\n"
            f"✨ **貢献度 (XP)**: {u.get('xp', 0):,} XP\n"
            f"📅 **システム登録**: {u.get('joined_at', '記録なし')}"
        )
        embed.add_field(name="Rb m/25 システムデータ", value=stats, inline=False)
        
        # 管理者判定（あなたのID）
        is_admin = "✅ 管理権限あり" if target.id == 840821281838202880 else "👤 一般ユーザー"
        embed.set_footer(text=f"権限区分: {is_admin} | Rb m/25")
        
        await it.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="システムの応答速度を確認します")
    async def ping(self, it: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await it.response.send_message(f"📡 **システム応答速度**: `{latency}ms`", ephemeral=True)

async def setup(bot):
    from __main__ import ledger_instance
    await bot.add_cog(Utility(bot, ledger_instance))
