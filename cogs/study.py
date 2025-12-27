import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone

# タイムゾーン設定
JST = timezone(timedelta(hours=9), 'JST')

class Study(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="study_start", description="学習を開始します")
    async def study_start(self, interaction: discord.Interaction):
        user_data = self.bot.ledger.get_user(interaction.user.id)
        
        if user_data.get("is_studying"):
            await interaction.response.send_message("⚠️ すでに学習記録が進行中です！", ephemeral=True)
            return

        user_data["is_studying"] = True
        user_data["study_start_time"] = datetime.now(JST).isoformat()
        self.bot.ledger.save()
        
        await interaction.response.send_message(f"📚 {interaction.user.display_name}さん、学習を開始しました！集中していきましょう。")

    @app_commands.command(name="study_end", description="学習を終了します")
    async def study_end(self, interaction: discord.Interaction):
        user_data = self.bot.ledger.get_user(interaction.user.id)
        
        if not user_data.get("is_studying"):
            await interaction.response.send_message("⚠️ 学習開始の記録が見つかりません。`/study_start` を先に実行してください。", ephemeral=True)
            return

        # 時間計算
        try:
            start_time = datetime.fromisoformat(user_data["study_start_time"])
        except (KeyError, ValueError):
            user_data["is_studying"] = False
            self.bot.ledger.save()
            return await interaction.response.send_message("❌ 開始時間のデータが破損していました。リセットしました。", ephemeral=True)

        end_time = datetime.now(JST)
        duration = end_time - start_time
        minutes = int(duration.total_seconds() / 60)

        # 不正・放置対策 (最大12時間 = 720分)
        if minutes > 720:
            minutes = 720
            over_notice = "\n⚠️ 12時間を超える記録のため、上限の720分として処理されました。"
        else:
            over_notice = ""

        if minutes < 1:
            user_data["is_studying"] = False
            self.bot.ledger.save()
            await interaction.response.send_message("⏱️ 1分未満の学習は記録されません。また頑張りましょう！")
            return

        # データの更新
        today = end_time.strftime("%Y-%m-%d")
        history = user_data.get("study_history", {})
        history[today] = history.get(today, 0) + minutes
        
        user_data["study_history"] = history
        user_data["total_study_time"] = user_data.get("total_study_time", 0) + minutes
        user_data["is_studying"] = False
        
        # 報酬設定 (1分につき1xp / 2分につき1cr)
        reward_cr = minutes // 2
        user_data["money"] = user_data.get("money", 0) + reward_cr
        user_data["xp"] = user_data.get("xp", 0) + minutes
        
        self.bot.ledger.save()

        h, m = divmod(minutes, 60)
        time_str = f"{h}時間{m}分" if h > 0 else f"{m}分"
        await interaction.response.send_message(
            f"✅ 学習終了！お疲れ様でした。\n"
            f"📖 今回の学習時間: **{time_str}**{over_notice}\n"
            f"💰 報酬: **{reward_cr} cr** / **{minutes} xp** を支給しました。"
        )

    @app_commands.command(name="study_stats", description="自分の学習統計を表示します")
    async def study_stats(self, interaction: discord.Interaction):
        user_data = self.bot.ledger.get_user(interaction.user.id)
        total_min = user_data.get("total_study_time", 0)
        history = user_data.get("study_history", {})
        
        today = datetime.now(JST).strftime("%Y-%m-%d")
        today_min = history.get(today, 0)

        embed = discord.Embed(
            title=f"📊 {interaction.user.display_name} の学習報告書", 
            color=0x42f56c,
            timestamp=datetime.now(JST)
        )
        
        # 現在の学習状況を表示
        if user_data.get("is_studying"):
            try:
                st = datetime.fromisoformat(user_data["study_start_time"])
                now_min = int((datetime.now(JST) - st).total_seconds() / 60)
                embed.add_field(name="✍️ 現在学習中", value=f"経過時間: **{now_min}分**", inline=False)
            except: pass

        th, tm = divmod(today_min, 60)
        all_h, all_m = divmod(total_min, 60)
        
        embed.add_field(name="📅 本日の記録", value=f"{th}時間{tm}分" if th > 0 else f"{tm}分", inline=True)
        embed.add_field(name="🏛️ 累計学習時間", value=f"{all_h}時間{all_m}分", inline=True)
        
        embed.set_footer(text="Rb m/25E 教育支援システム")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="study_ranking", description="学習時間のランキングを表示します")
    @app_commands.describe(span="表示する期間（daily, weekly, monthly, total）")
    async def study_ranking(self, interaction: discord.Interaction, span: str = "total"):
        await interaction.response.defer()

        if span not in ["daily", "weekly", "monthly", "total"]:
            return await interaction.followup.send("❌ 引数は daily, weekly, monthly, total から選択してください。")

        ranking_data = []
        now = datetime.now(JST)
        
        # main.pyの設計に合わせ .data["users"] を参照
        users_dict = self.bot.ledger.data.get("users", {})

        for user_id_str, data in users_dict.items():
            try:
                user_id = int(user_id_str)
            except ValueError: continue

            time_val = 0
            if span == "total":
                time_val = data.get("total_study_time", 0)
            else:
                history = data.get("study_history", {})
                for date_str, minutes in history.items():
                    try:
                        log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        target_date = now.date()
                        diff = (target_date - log_date).days
                        
                        if span == "daily" and diff == 0:
                            time_val += minutes
                        elif span == "weekly" and diff < 7:
                            time_val += minutes
                        elif span == "monthly" and diff < 30:
                            time_val += minutes
                    except ValueError: continue
            
            if time_val > 0:
                ranking_data.append({"user_id": user_id, "time": time_val})

        if not ranking_data:
            return await interaction.followup.send(f"⚠️ {span} の有効なランキングデータがありません。")

        ranking_data.sort(key=lambda x: x["time"], reverse=True)

        embed = discord.Embed(
            title=f"🏆 学習ランキング [{span.upper()}]",
            color=0xffd700,
            timestamp=now
        )

        desc = ""
        for i, item in enumerate(ranking_data[:10], 1):
            user_id = item["user_id"]
            member = interaction.guild.get_member(user_id)
            name = member.display_name if member else f"User({user_id})"

            h, m = divmod(item["time"], 60)
            time_str = f"{h}h {m}m" if h > 0 else f"{m}m"
            
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"`{i}.`")
            desc += f"{medal} **{name}**: {time_str}\n"

        embed.description = desc
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Study(bot))
