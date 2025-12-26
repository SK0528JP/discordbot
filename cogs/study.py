import discord
from discord import app_commands
from discord.ext import commands
import time

class Study(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # ユーザーID: 開始時間の辞書
        self.active_sessions = {}

    @app_commands.command(name="study_start", description="学習任務を開始します。")
    async def study_start(self, interaction: discord.Interaction):
        # 応答を保留（「考え中...」にして3秒タイムアウトを防ぐ）
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        
        if user_id in self.active_sessions:
            await interaction.followup.send("⚠️ 既に学習任務に就いています。一旦終了してください。")
            return

        # 開始時間を記録
        self.active_sessions[user_id] = time.time()
        
        embed = discord.Embed(
            title="🚀 学習任務開始",
            description=f"同志 {interaction.user.display_name}、戦線へようこそ。\n集中力を維持し、目標を完遂せよ。",
            color=discord.Color.blue()
        )
        embed.set_timestamp()
        # deferした後は followup.send を使う
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="study_end", description="学習任務を終了し、成果を記録します。")
    async def study_end(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        
        if user_id not in self.active_sessions:
            await interaction.followup.send("❌ 学習任務が開始されていません。")
            return

        # 経過時間を計算（秒 -> 分）
        start_time = self.active_sessions.pop(user_id)
        elapsed_seconds = int(time.time() - start_time)
        minutes = elapsed_seconds // 60
        
        # 累積時間の記録
        total_time_display = "記録エラー"
        if self.bot.ledger:
            try:
                user_data = self.bot.ledger.get_user(interaction.user.id)
                if "total_study_time" not in user_data:
                    user_data["total_study_time"] = 0
                
                user_data["total_study_time"] += minutes
                self.bot.ledger.save()
                total_time_display = f"{user_data['total_study_time']} 分"
            except Exception as e:
                print(f"Ledger Save Error: {e}")

        embed = discord.Embed(
            title="🏁 学習任務完了",
            description=f"同志 {interaction.user.display_name}、帰還を歓迎する。",
            color=discord.Color.green()
        )
        embed.add_field(name="今回の戦果", value=f"**{minutes} 分**", inline=True)
        embed.add_field(name="累積学習時間", value=f"**{total_time_display}**", inline=True)
        embed.set_footer(text="Fika（休憩）を挟み、次の作戦に備えよ。")
        embed.set_timestamp()
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Study(bot))
