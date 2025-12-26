import discord
from discord import app_commands
from discord.ext import commands
import time
from datetime import datetime, timedelta, timezone
import io

# グラフ機能用（インストールされている場合のみ動作）
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# タイムゾーン定義
JST = timezone(timedelta(hours=9), 'JST')

class Study(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def create_study_graph(self, history, days=7):
        if not HAS_MATPLOTLIB:
            return None
        try:
            now_jst = datetime.now(JST)
            dates = []
            minutes = []
            for i in range(days - 1, -1, -1):
                d = (now_jst - timedelta(days=i))
                d_str = d.strftime("%Y-%m-%d")
                dates.append(d)
                minutes.append(history.get(d_str, 0))

            plt.figure(figsize=(8, 4))
            plt.style.use('dark_background')
            plt.bar(dates, minutes, color='#5865F2')
            plt.title(f"Study Time (Last {days} days)", fontsize=15)
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            plt.gca().xaxis.set_major_locator(mdates.DayLocator())
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            buf.seek(0)
            plt.close()
            return buf
        except Exception as e:
            print(f"Graph Error: {e}")
            return None

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
            description=f"同志 {interaction.user.display_name}、戦線へようこそ。\n集中力を維持し、目標を完遂せよ。",
            color=discord.Color.blue(),
            timestamp=datetime.now(JST)
        )
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
        
        if "study_history" not in user_data:
            user_data["study_history"] = {}
        
        user_data["study_history"][today_str] = user_data["study_history"].get(today_str, 0) + elapsed_minutes
        user_data["total_study_time"] = user_data.get("total_study_time", 0) + elapsed_minutes
        user_data["study_start_time"] = None
        self.bot.ledger.save()

        embed = discord.Embed(
            title="🏁 学習任務完了",
            description=f"同志 {interaction.user.display_name}、帰還を歓迎する。",
            color=discord.Color.green(),
            timestamp=now_jst
        )
        embed.add_field(name="今回の戦果", value=f"**{elapsed_minutes} 分**", inline=True)
        embed.add_field(name="本日の合計", value=f"**{user_data['study_history'][today_str]} 分**", inline=True)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="study_stats", description="学習統計とグラフを表示します。")
    @app_commands.choices(period=[
        app_commands.Choice(name="今日", value="today"),
        app_commands.Choice(name="今週（グラフ表示）", value="week"),
        app_commands.Choice(name="今月", value="month"),
        app_commands.Choice(name="全期間", value="all")
    ])
    async def study_stats(self, interaction: discord.Interaction, period: str = "today"):
        await interaction.response.defer()
        user_data = self.bot.ledger.get_user(interaction.user.id)
        history = user_data.get("study_history", {})
        now_jst = datetime.now(JST)
        
        total = 0
        file = None

        if period == "today":
            total = history.get(now_jst.strftime("%Y-%m-%d"), 0)
            period_label = "今日"
        elif period == "all":
            total = user_data.get("total_study_time", 0)
            period_label = "全期間"
        else:
            days = 7 if period == "week" else 30
            for i in range(days):
                d_str = (now_jst - timedelta(days=i)).strftime("%Y-%m-%d")
                total += history.get(d_str, 0)
            period_label = f"直近 {days} 日間"
            
            if period == "week" and HAS_MATPLOTLIB:
                buf = self.create_study_graph(history, days=7)
                if buf: file = discord.File(buf, filename="study_graph.png")

        embed = discord.Embed(title=f"📊 学習統計: {period_label}", color=discord.Color.purple(), timestamp=now_jst)
        embed.add_field(name="期間内合計", value=f"**{total} 分**", inline=True)
        embed.add_field(name="全累計", value=f"**{user_data.get('total_study_time', 0)} 分**", inline=True)
        
        if file:
            embed.set_image(url="attachment://study_graph.png")
            await interaction.followup.send(embed=embed, file=file)
        else:
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="study_ranking", description="学習時間のランキングを表示します。")
    @app_commands.choices(period=[
        app_commands.Choice(name="今日", value="today"),
        app_commands.Choice(name="今週", value="week"),
        app_commands.Choice(name="今月", value="month"),
        app_commands.Choice(name="全期間", value="all")
    ])
    async def study_ranking(self, interaction: discord.Interaction, period: str = "week"):
        await interaction.response.defer()
        if not self.bot.ledger:
            await interaction.followup.send("❌ データにアクセスできません。")
            return

        all_users = self.bot.ledger.data
        ranking_data = []
        now_jst = datetime.now(JST)
        days = 1 if period == "today" else 7 if period == "week" else 30 if period == "month" else 9999
        period_label = "今日" if period == "today" else f"直近 {days} 日間" if period != "all" else "全期間"

        for u_id, data in all_users.items():
            try:
                score = 0
                if period == "all":
                    score = data.get("total_study_time", 0)
                else:
                    hist = data.get("study_history", {})
                    for i in range(days):
                        d_str = (now_jst - timedelta(days=i)).strftime("%Y-%m-%d")
                        score += hist.get(d_str, 0)
                if score > 0:
                    ranking_data.append({"id": int(u_id), "time": score})
            except: continue

        ranking_data.sort(key=lambda x: x["time"], reverse=True)
        if not ranking_data:
            await interaction.followup.send(f"⚠️ {period_label} の記録がある同志はいません。")
            return

        embed = discord.Embed(title=f"🏆 学習ランキング ({period_label})", color=discord.Color.gold(), timestamp=now_jst)
        desc = ""
        for i, entry in enumerate(ranking_data[:10], 1):
            member = interaction.guild.get_member(entry['id'])
            if not member:
                try: user = await self.bot.fetch_user(entry['id']); name = user.display_name
                except: name = f"未知の同志({entry['id']})"
            else: name = member.display_name
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`{i}.`"
            desc += f"{medal} **{name}**: {entry['time']} 分\n"

        embed.description = desc
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Study(bot))
