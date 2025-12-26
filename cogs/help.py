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
        システムの全体像と、各専門モジュールの役割を詳細に案内します。
        """
        embed = discord.Embed(
            title="🌿 Rb m/25 System Manual",
            description=(
                "Rb m/25 は複数の専門ユニットで構成されたインフラシステムです。\n"
                "以下に現在稼働中の主要コマンドを一覧表示します。"
            ),
            color=0x475569
        )

        # 👤 User & Status
        embed.add_field(
            name="👤 User & Status",
            value="`/status` : 自分の資産・貢献度をクイック照会\n`/user` : IDやメンションから全公開情報を精密調査",
            inline=False
        )
        
        # 💎 Economy & Exchange (ここを更新)
        embed.add_field(
            name="💎 Economy & Exchange",
            value=(
                "`/pay` : 他のユーザーへ資産を安全に送金\n"
                "`/ranking` : 資産・貢献度のサーバー内順位を表示\n"
                "`/exchange` : **[NEW]** 貯めたXPを資産(cr)に換金"
            ),
            inline=False
        )
        
        # 🎡 Entertainment & Game
        embed.add_field(
            name="🎡 Entertainment & Game",
            value="`/roulette` : 公平な抽選の実行\n`/janken` : じゃんけん勝負（報酬あり）\n`/fortune` : 本日の運勢診断",
            inline=False
        )
        
        # 🛰️ Infrastructure
        embed.add_field(
            name="🛰️ Infrastructure",
            value="`/ping` : ネットワーク品質とAPI応答速度の診断\n`/help` : このシステムマニュアルを表示",
            inline=False
        )

        # 管理者向け情報
        if it.user.id == 840821281838202880:
            embed.add_field(
                name="🔑 Administrator Only",
                value="`/admin_grant` : 資産付与\n`/admin_confiscate` : 資産没収\n`/restart` : システム再起動",
                inline=False
            )

        embed.set_author(name="Rb m/25 Interface Terminal", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Rb m/25 Documentation Unit | Reliability and Transparency")
        
        # ヘルプは自分だけに表示されるように設定
        await it.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    from __main__ import ledger_instance
    await bot.add_cog(Help(bot, ledger_instance))
