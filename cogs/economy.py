import discord
from discord.ext import commands
from discord import app_commands

class Economy(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="ranking", description="労働英雄ランキング")
    async def ranking(self, it: discord.Interaction):
        sorted_users = sorted(self.ledger.data.items(), key=lambda x: x[1].get("xp", 0), reverse=True)[:10]
        embed = discord.Embed(title="🏆 労働英雄ランキング (XP)", color=0xffd700)
        
        description = ""
        for i, (uid, stats) in enumerate(sorted_users, 1):
            name = f"<@{uid}>"
            description += f"**{i}位**: {name} ― `{stats['xp']}` XP\n"
        
        embed.description = description
        await it.response.send_message(embed=embed)

    # ... 他の pay, exchange 等も同様に Embed でラップ（以前のコードのロジックを維持）
