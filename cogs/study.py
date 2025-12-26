import discord
from discord import app_commands
from discord.ext import commands
import time
from datetime import datetime

class Study(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 勉強中ユーザーの開始時間を一時的に保持 (UserID: StartTime)
        self.active_sessions = {}

    @app_commands.command(name="study_start", description="学習任務を開始します。")
    async def study_start(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        if user_id in self.active_sessions:
            await interaction.response.send_message("⚠️ 既に学習任務に就いています。一旦終了してください。", ephemeral=True)
            return

        # UNIXタイムスタンプで開始時間を記録
        self.active_sessions[user_id] = time.time()
        
        embed = discord.Embed(
            title="🚀 学習任務開始",
            description=f"同志 {interaction.user.display_name}、戦線へようこそ。\n集中力を維持し、目標を完遂せよ。",
            color=discord.Color.blue()
        )
        embed.set_timestamp()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="study_end", description="学習任務を終了し、成果を記録します。")
    async def study_end(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        if user_id not in self.active_sessions:
            await interaction.response.send_message("❌ 学習任務が開始されていません。", ephemeral=True)
            return

        # 経過時間を計算（秒 -> 分）
        start_time = self.active_sessions.pop(user_id)
        elapsed_seconds = int(time.time() - start_time)
        minutes = elapsed_seconds // 60
        
        # Ledgerに保存するための処理
        if self.bot.ledger:
            user_data = self.bot.ledger.get_user(interaction.user.id)
            
            # 既存のデータに 'total_study_time' がなければ 0 で初期化
            if "total_study_time" not in user_data:
                user_data["total_study_time"] = 0
            
            user_data["total_study_time"] += minutes
            self.bot.ledger.save() # Gistへ保存
            
            total_time = user_data["total_study_time"]
        else:
            total_time = "記録失敗(Ledger無効)"

        embed = discord.Embed(
            title="🏁 学習任務完了",
            description=f"同志 {interaction.user.display_name}、帰還を歓迎する。",
            color=discord.Color.green()
        )
        embed.add_field(name="今回の戦果", value=f"**{minutes} 分**", inline=True)
        embed.add_field(name="累積学習時間", value=f"**{total_time} 分**", inline=True)
        embed.set_footer(text="Fika（休憩）を挟み、次の作戦に備えよ。")
        embed.set_timestamp()
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Study(bot))
