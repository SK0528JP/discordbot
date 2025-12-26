import discord
from discord import app_commands
from discord.ext import commands
import time
from datetime import datetime, timedelta, timezone

# タイムゾーン
JST = timezone(timedelta(hours=9), 'JST')

class Study(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- 既存の start / end / stats コマンドはそのまま維持 ---

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
        embed = discord.Embed(title="🚀 学習任務開始", description=f"同志 {interaction.user.display_name}、戦線へようこそ。", color=discord.Color.blue(), timestamp=datetime.now(JST))
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="study_end", description="学習任務を終了し、履歴を記録します。")
    async def study_end(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user_data = self.bot.ledger.get_user(interaction.user.id)
        start_time = user_data.get("study_start_time")
        if not start_time:
            await interaction.followup.send("❌ 学習任務が開始されていません。")
            return
        elapsed_minutes = int((time.time() - start_time) // 60)
        now_jst = datetime.now(JST)
        today_str = now_jst.strftime("%Y-%m-%d")
        if "study_history" not in user_data: user_data["study_history"] = {}
        user_data["study_history"][today_str] = user_data["study_history"].get(today_str, 0) + elapsed_minutes
        user_data["total_study_time"] = user_data.get("total_study_time", 0) + elapsed_minutes
        user_data["study_start_time"] = None
        self.bot.ledger.save()
        embed = discord.Embed(title="🏁 学習任務完了", color=discord.Color.green(), timestamp=now_jst)
        embed.add_field(name="今回の戦果", value=f"{elapsed_minutes} 分", inline=True)
        embed.add_field(name="本日の合計", value=f"{user_data['study_history'][today_str]} 分", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="study_stats", description="個人の学習統計を表示します。")
    async def study_stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user_data = self.bot.ledger.get_user(interaction.user.id)
        total = user_data.get("total_study_time", 0)
        embed = discord.Embed(title=f"📊 同志 {interaction.user.display_name} の統計", color=discord.Color.purple(), timestamp=datetime.now(JST))
        embed.add_field(name="全累計時間", value=f"**{total} 分**", inline=True)
        await interaction.followup.send(embed=embed)

    # --- ✨ 新機能: ランキングコマンド ---
    @app_commands.command(name="study_ranking", description="学習時間のランキングを表示します。")
    @app_commands.choices(period=[
        app_commands.Choice(name="今日", value="today"),
        app_commands.Choice(name="今週（直近7日）", value="week"),
        app_commands.Choice(name="今月（直近30日）", value="month"),
        app_commands.Choice(name="全期間", value="all")
    ])
    async def study_ranking(self, interaction: discord.Interaction, period: str = "week"):
        await interaction.response.defer()
        
        if not self.bot.ledger:
            await interaction.followup.send("❌ データにアクセスできません。")
            return

        all_users = self.bot.ledger.data # Ledger内の全ユーザーデータ
        ranking = []
        now_jst = datetime.now(JST)
        
        # 期間の設定
        days = 1 if period == "today" else 7 if period == "week" else 30 if period == "month" else 9999
        period_label = "今日" if period == "today" else f"直近 {days} 日間" if period != "all" else "全期間"

        for user_id, data in all_users.items():
            total_minutes = 0
            if period == "all":
                total_minutes = data.get("total_study_time", 0)
            else:
                history = data.get("study_history", {})
                for i in range(days):
                    date_str = (now_jst - timedelta(days=i)).strftime("%Y-%m-%d")
                    total_minutes += history.get(date_str, 0)
            
            if total_minutes > 0:
                ranking.append({"id": user_id, "time": total_minutes})

        # 学習時間で降順ソート
        ranking.sort(key=lambda x: x["time"], reverse=True)

        if not ranking:
            await interaction.followup.send(f"⚠️ {period_label} の記録がある同志はまだいないようだ。")
            return

        embed = discord.Embed(
            title=f"🏆 学習時間ランキング ({period_label})",
            color=discord.Color.gold(),
            timestamp=now_jst
        )

        description = ""
        for i, entry in enumerate(ranking[:10], 1): # 上位10名
            member = interaction.guild.get_member(int(entry['id']))
            name = member.display_name if member else f"未知の同志({entry['id']})"
            
            # メダル絵文字
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`{i}.`"
            description += f"{medal} **{name}**: {entry['time']} 分\n"

        embed.description = description
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Study(bot))
