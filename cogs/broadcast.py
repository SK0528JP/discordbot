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
        await it.response.send_message("❌ アクセス拒否：最高管理者権限が必要です。", ephemeral=True)
        return False

    @app_commands.command(name="broadcast", description="[管理者専用] 全導入サーバーへ種別を選択して一斉放送を行います")
    @app_commands.describe(
        mode="放送種別（通常 / 告知 / 緊急）",
        message="放送内容",
        mention_all="全員にメンションを飛ばすか（⚠️慎重に使用してください）"
    )
    @app_commands.choices(mode=[
        app_commands.Choice(name="⚪ 通常（Information）", value="info"),
        app_commands.Choice(name="🟡 告知（Warning）", value="warn"),
        app_commands.Choice(name="🔴 緊急（Emergency）", value="emerg")
    ])
    async def broadcast(
        self, 
        it: discord.Interaction, 
        mode: str, 
        message: str, 
        mention_all: bool = False
    ):
        if not await self.is_admin(it): return
        
        await it.response.defer(ephemeral=True)

        # モードに応じたビジュアル設定
        config = {
            "info":  {"color": 0x3498db, "title": "📡 Rb m/25E 全域通常放送", "icon": "🔵"},
            "warn":  {"color": f1c40f, "title": "⚠️ Rb m/25E 全域告知放送", "icon": "🟡"},
            "emerg": {"color": 0xe74c3c, "title": "🚨 Rb m/25E 全域緊急放送", "icon": "🔴"}
        }
        current_cfg = config.get(mode)

        # 動的な発信元情報の取得
        origin_guild = it.guild.name if it.guild else "Direct Link (HQ)"
        sender_name = it.user.global_name or it.user.name

        # 放送用Embedの構築
        embed = discord.Embed(
            title=f"{current_cfg['icon']} {current_cfg['title']}",
            description=message,
            color=current_cfg['color'],
            timestamp=datetime.now()
        )
        embed.set_author(name=f"発信者: {sender_name}", icon_url=it.user.display_avatar.url)
        embed.add_field(name="🛰️ 発信元", value=f"`{origin_guild}`", inline=True)
        embed.add_field(name="🆔 ID", value=f"`RMS-{datetime.now().strftime('%Y%m%d%H%M')}`", inline=True)
        embed.set_footer(text=f"Rb m/25 Global Relay System | ターゲット: {len(self.bot.guilds)} サーバー")

        success_count = 0
        total_viewers = 0
        
        for guild in self.bot.guilds:
            # 送信先チャンネルの選定
            target = guild.system_channel if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages else None
            
            if not target:
                # システムチャンネルがない場合は、最初の書き込み可能なチャンネルを探す
                for ch in guild.text_channels:
                    if ch.permissions_for(guild.me).send_messages:
                        target = ch
                        break
            
            if target:
                try:
                    content = "@everyone" if mention_all else None
                    await target.send(content=content, embed=embed)
                    success_count += 1
                    total_viewers += guild.member_count
                except:
                    pass

        # 司令官への完了報告
        report = discord.Embed(
            title="✅ 全域パケット送信完了",
            description=f"指定されたメッセージの全域放送を完了しました。",
            color=0x2ecc71
        )
        report.add_field(name="ステータス", value=f"成功: `{success_count}` / 全体: `{len(self.bot.guilds)}`", inline=True)
        report.add_field(name="影響範囲", value=f"推定到達人数: `{total_viewers}`名", inline=True)
        report.add_field(name="メンション", value="`有効`" if mention_all else "`無効`", inline=True)
        
        await it.followup.send(embed=report, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Broadcast(bot))
