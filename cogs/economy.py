import discord
from discord.ext import commands
from discord import app_commands
from strings import STRINGS

class Economy(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="ranking", description="View rankings / ランキング表示 / Visa rankning")
    @app_commands.choices(type=[
        app_commands.Choice(name="Contribution (XP)", value="xp"),
        app_commands.Choice(name="Wealth (Money)", value="money"),
    ])
    async def ranking(self, it: discord.Interaction, type: str = "xp"):
        u = self.ledger.get_user(it.user.id)
        lang = u.get("lang", "ja")
        s = STRINGS[lang]

        # データのソート
        all_users = self.ledger.data
        sorted_users = sorted(
            all_users.items(), 
            key=lambda x: x[1].get(type, 0), 
            reverse=True
        )[:10]

        title = s["rank_xp_title"] if type == "xp" else s["rank_money_title"]
        embed = discord.Embed(title=title, description=s["rank_desc"], color=0x94a3b8)
        
        rank_list = ""
        for i, (uid, stats) in enumerate(sorted_users, 1):
            # サーバー内メンバーの名前取得を試みる
            member = it.guild.get_member(int(uid))
            name = member.display_name if member else f"User_{uid[:4]}"
            
            val = stats.get(type, 0)
            unit = "XP" if type == "xp" else "cr"
            
            # 言語別順位表記
            suffix = {"ja": "位", "en": "th", "sv": ":a"}.get(lang, "")
            # 英語の1st, 2nd, 3rd例外処理
            if lang == "en":
                if i == 1: suffix = "st"
                elif i == 2: suffix = "nd"
                elif i == 3: suffix = "rd"

            rank_list += f"`{i}{suffix}` **{name}** : {val:,} {unit}\n"
        
        embed.add_field(name="Leaderboard", value=rank_list or "No data available.", inline=False)
        embed.set_footer(text=s["footer_finance"])
        await it.response.send_message(embed=embed)

    @app_commands.command(name="pay", description="Transfer credits / 送金 / Överför")
    @app_commands.describe(target="Recipient", amount="Amount to send")
    async def pay(self, it: discord.Interaction, target: discord.Member, amount: int):
        u_sender = self.ledger.get_user(it.user.id)
        lang = u_sender.get("lang", "ja")
        s = STRINGS[lang]

        if target.bot:
            await it.response.send_message("❌ Cannot transfer to bots.", ephemeral=True)
            return

        if amount <= 0 or u_sender["money"] < amount:
            msg = {"ja": "残高不足または不正な数値です。", "en": "Insufficient funds or invalid amount.", "sv": "Otillräckliga medel."}
            await it.response.send_message(f"❌ {msg[lang]}", ephemeral=True)
            return

        u_target = self.ledger.get_user(target.id)
        u_sender["money"] -= amount
        u_target["money"] += amount
        self.ledger.save()

        embed = discord.Embed(title=s["pay_success"], color=0x88a096)
        embed.add_field(name="Sender", value=it.user.display_name, inline=True)
        embed.add_field(name="Recipient", value=target.display_name, inline=True)
        embed.add_field(name="Amount", value=f"**{amount:,}** credits", inline=False)
        embed.set_footer(text=s["footer_finance"])
        await it.response.send_message(embed=embed)

async def setup(bot):
    from __main__ import ledger_instance
    await bot.add_cog(Economy(bot, ledger_instance))
