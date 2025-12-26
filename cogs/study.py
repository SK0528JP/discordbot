import discord
from discord import app_commands
from discord.ext import commands
import time
from datetime import datetime

class Study(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="study_start", description="学習任務を開始します。")
    async def study_start(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if not self.bot.ledger:
            await interaction.followup.send("❌ Ledgerが有効ではありません。")
            return

        user_data = self.bot.ledger.get_user(interaction.user.id)
        if user_data.get("study_start_time"):
            await interaction.followup.send("⚠️ 既に学習任務に就いています。")
            return

        user_data["study_start_time"] = time.time()
        self.bot.ledger.save()
        
        embed = discord.Embed(
            title="🚀 学習任務開始",
            description=f"同志 {interaction.user.display_name}、戦線へようこそ。",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="study_end", description="学習任務を終了し、成果を記録します。")
    async def study_end(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user_data = self.bot.ledger.get_user(interaction.user.id)
        start_time = user_data.get("study_start_time")
        
        if not start_time:
            await interaction.followup.send("❌ 学習任務が開始されていません。")
            return

        elapsed_minutes = int((time.time() - start_time) // 60)
        user_data["total_study_time"] = user_data.get("total_study_time", 0) + elapsed_minutes
        user_data["study_start_time"] = None
        self.bot.ledger.save()

        embed = discord.Embed(
            title="🏁 学習任務完了",
            description=f"同志 {interaction.user.display_name}、お疲れ様だ。",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="今回の戦果", value=f"{elapsed_minutes} 分", inline=True)
        embed.add_field(name="累積学習時間", value=f"{user_data['total_study_time']} 分", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="study_stats", description="自分のこれまでの累積学習時間を確認します。")
    async def study_stats(self, interaction: discord.Interaction):
        """累積学習時間を表示する新コマンド"""
        user_data = self.bot.ledger.get_user(interaction.user.id)
        total_time = user_data.get("total_study_time", 0)
        is_studying = "🔴 学習任務中" if user_data.get("study_start_time") else "⚪ 待機中"

        embed = discord.Embed(
            title=f"📊 同志 {interaction.user.display_name} の学習統計",
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )
        embed.add_field(name="現在の状態", value=is_studying, inline=False)
        embed.add_field(name="総学習時間", value=f"**{total_time} 分**", inline=False)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Study(bot))
