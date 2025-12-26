import discord
from discord.ext import commands
from discord import app_commands
import random
from strings import STRINGS

class Entertainment(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="janken", description="Play Rock Paper Scissors / じゃんけん / Sten, Sax, Påse")
    @app_commands.describe(choice="Your hand / 自分の手 / Din hand")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Rock / 👊 / Sten", value="rock"),
        app_commands.Choice(name="Paper / ✋ / Påse", value="paper"),
        app_commands.Choice(name="Scissors / ✌️ / Sax", value="scissors"),
    ])
    async def janken(self, it: discord.Interaction, choice: app_commands.Choice[str]):
        u = self.ledger.get_user(it.user.id)
        lang = u.get("lang", "ja")
        s = STRINGS[lang]
        
        bot_choice = random.choice(["rock", "paper", "scissors"])
        hands = {
            "rock": "👊",
            "paper": "✋",
            "scissors": "✌️"
        }

        # 勝敗判定
        if choice.value == bot_choice:
            result_key = "janken_tie"
            color = 0x94a3b8
        elif (choice.value == "rock" and bot_choice == "scissors") or \
             (choice.value == "paper" and bot_choice == "rock") or \
             (choice.value == "scissors" and bot_choice == "paper"):
            result_key = "janken_win"
            color = 0x2ecc71
            # 勝利報酬
            u["money"] += 10
            self.ledger.save()
        else:
            result_key = "janken_lose"
            color = 0xe74c3c

        embed = discord.Embed(title="Rb m/25 Janken Unit", color=color)
        embed.add_field(name="YOU", value=f"{hands[choice.value]} ({choice.name})", inline=True)
        embed.add_field(name="BOT", value=f"{hands[bot_choice]}", inline=True)
        embed.add_field(name="Result", value=f"**{s[result_key]}**", inline=False)
        
        if result_key == "janken_win":
            embed.set_footer(text="+10 credits awarded.")
            
        await it.response.send_message(embed=embed)

    @app_commands.command(name="fortune", description="Draw a fortune / おみくじ / Dra en lyckosedel")
    async def fortune(self, it: discord.Interaction):
        u = self.ledger.get_user(it.user.id)
        lang = u.get("lang", "ja")
        s = STRINGS[lang]

        # 言語別の結果リスト (strings.pyに定義がない場合を想定して直接定義)
        results = {
            "ja": ["大吉", "中吉", "小吉", "吉", "末吉", "凶"],
            "en": ["Great Blessing", "Middle Blessing", "Small Blessing", "Blessing", "Future Blessing", "Curse"],
            "sv": ["Stor Välsignelse", "Mellan Välsignelse", "Liten Välsignelse", "Välsignelse", "Framtida Välsignelse", "Förbannelse"]
        }
        
        res = random.choice(results.get(lang, results["en"]))
        
        embed = discord.Embed(title="Rb m/25 Fortune Unit", color=0x6366f1)
        embed.description = f"✨ {s['fortune_result']}: **{res}**"
        embed.set_footer(text=s["footer_admin"])
        
        await it.response.send_message(embed=embed)

async def setup(bot):
    from __main__ import ledger_instance
    await bot.add_cog(Entertainment(bot, ledger_instance))
