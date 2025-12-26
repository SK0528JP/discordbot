import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9), 'JST')

class Ranking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ranking", description="各種ランキングを表示します")
    @app_commands.choices(category=[
        app_commands.Choice(name="資産 (Credits)", value="money"),
        app_commands.Choice(name="貢献度 (XP)", value="xp"),
        app_commands.Choice(name="釣り (最大サイズ)", value="fishing"),
        app_commands.Choice(name="学習 (累計時間)", value="study"),
    ])
    async def ranking(self, it: discord.Interaction, category: str):
        # 応答を保留（考え中状態にして3秒ルールを回避）
        await it.response.defer()

        all_users = self.bot.ledger.data
        if not all_users:
            await it.followup.send("📊 まだデータが蓄積されていません。")
            return

        ranking_data = []

        # データ抽出ロジック
        for uid_str, data in all_users.items():
            try:
                uid = int(uid_str)
            except:
                continue

            val = 0
            label = ""

            if category == "money":
                val = data.get("money", 0)
                label = f"{val:,} cr"
            elif category == "xp":
                val = data.get("xp", 0)
                label = f"{val:,} xp"
            elif category == "fishing":
                inventory = data.get("fishing_inventory", [])
                if inventory:
                    # 持っている魚の中で最大サイズを探す
                    max_fish = max(inventory, key=lambda x: x["size"])
                    val = max_fish["size"]
                    label = f"{max_fish['name']} ({val} cm)"
            elif category == "study":
                val = data.get("total_study_time", 0)
                h, m = divmod(val, 60)
                label = f"{h}h {m}m"

            if val > 0:
                ranking_data.append({"uid": uid, "val": val, "label": label})

        if not ranking_data:
            await it.followup.send(f"⚠️ {category} のデータを持っているユーザーがいません。")
            return

        # ソート（降順）
        ranking_data.sort(key=lambda x: x["val"], reverse=True)

        embed = discord.Embed(title=f"🏆 {category.capitalize()} ランキング", color=0xffd700)
        
        lines = []
        for i, item in enumerate(ranking_data[:10], 1):
            member = it.guild.get_member(item["uid"])
            name = member.display_name if member else self.bot.get_user(item["uid"])
            name = name if name else f"User_{str(item['uid'])[:4]}"
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`{i}.`"
            lines.append(f"{medal} **{name}**: {item['label']}")

        embed.description = "\n".join(lines)
        embed.set_footer(text="Rb m/25 Ranking System")
        
        await it.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Ranking(bot))
