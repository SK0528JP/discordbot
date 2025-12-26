import discord
from discord.ext import commands
from discord import app_commands

class Help(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="help", description="Rb m/25 の全コマンドと操作ガイドを表示します")
    async def help_command(self, it: discord.Interaction):
        """
        システムの全体像と、各モジュールの役割を詳細に案内します。
        """
        embed = discord.Embed(
            title="🌿 Rb m/25 System Manual",
            description=(
                "Rb m/25 は複数の専門モジュールで構成されたサーバー管理インフラです。\n"
                "以下に現在稼働中の主要コマンドを一覧表示します。"
            ),
            color=0x475569
        )

        # セクションごとに整理
        embed.add_field(
            name="👤 User & Status",
            value="`/status` : 自分の簡易ステータスを表示\n`/user` : ユーザーIDやメンションから詳細を精密調査",
            inline=False
        )
        
        embed.add_field(
            name="💰 Economy",
            value="`/pay` : ユーザー間での資産送金\n`/ranking` : 資産・XPのトップ10を表示",
            inline=False
        )
        
        embed.add_field(
            name="🎡 Entertainment & Game",
            value="`/roulette` : 複数候補からの公平な抽選\n`/janken` : じゃんけん勝負(報酬あり)\n`/fortune` : 本日の運勢",
            inline=False
        )
        
        embed.add_field(
            name="🛰️ Infrastructure",
            value="`/ping` : ネットワーク品質とAPI応答速度の診断",
            inline=False
        )

        # 管理者向け情報は、管理者のみに見えるように文言を調整するか、あるいはシンプルに記載
        if it.user.id == 840821281838202880:
            embed.add_field(
                name="🔑 Administrator Only",
                value="`/admin_grant` : 資産の付与\n`/admin_confiscate` : 資産の没収\n`/restart` : システムの強制再起動",
                inline=False
            )

        embed.set_author(name="Rb m/25 Interface Terminal", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Rb m/25 Documentation Unit | Reliability and Transparency")
        
        await it.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    from __main__ import ledger_instance
    await bot.add_cog(Help(bot, ledger_instance))
