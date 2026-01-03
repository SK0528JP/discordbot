import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

class Broadcast(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 管理権限を持つユーザーID
        self.ADMIN_USER_IDS = [840821281838202880]

    async def is_admin(self, it: discord.Interaction):
        if it.user.id in self.ADMIN_USER_IDS:
            return True
        await it.response.send_message("❌ このコマンドは最高管理者のみが実行可能です。", ephemeral=True)
        return False

    @app_commands.command(name="broadcast", description="[管理者専用] 導入済みの全サーバーへ一斉放送を行います")
    @app_commands.describe(message="放送するメッセージ内容", title="放送のタイトル")
    async def broadcast(self, it: discord.Interaction, message: str, title: str = "📡 Rb m/25E 全域緊急放送"):
        if not await self.is_admin(it): return
        
        # 応答を保留（時間がかかる可能性があるため）
        await it.response.defer(ephemeral=True)

        guilds = self.bot.guilds
        success_count = 0
        total_viewers = 0
        failed_guilds = []

        # 放送用Embedの構築
        embed = discord.Embed(
            title=title,
            description=message,
            color=0xe74c3c, # 緊急放送用の赤
            timestamp=datetime.now()
        )
        embed.set_author(name="Rb m/25E Global Command", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="送信元: 瑞典工業設計局 | 指揮官直属プロトコル")

        for guild in guilds:
            target_channel = None
            
            # 1. システムチャンネルを優先
            if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
                target_channel = guild.system_channel
            else:
                # 2. 送信可能なテキストチャンネルを検索
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        target_channel = channel
                        break
            
            if target_channel:
                try:
                    await target_channel.send(embed=embed)
                    success_count += 1
                    total_viewers += guild.member_count
                except Exception as e:
                    failed_guilds.append(f"{guild.name} ({e})")
            else:
                failed_guilds.append(f"{guild.name} (有効なチャンネルなし)")

        # 司令官への最終報告
        report_embed = discord.Embed(
            title="✅ 全域放送完了報告",
            color=0x2ecc71,
            timestamp=datetime.now()
        )
        report_embed.add_field(name="成功サーバー数", value=f"`{success_count}` / `{len(guilds)}`", inline=True)
        report_embed.add_field(name="推定到達人数", value=f"`{total_viewers}`名", inline=True)
        
        if failed_guilds:
            report_embed.add_field(name="失敗/スキップ", value="\n".join(failed_guilds[:5]), inline=False)

        await it.followup.send(embed=report_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Broadcast(bot))
