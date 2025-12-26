import discord
from discord.ext import commands
from discord import app_commands

class Economy(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    # --- /pay ---
    @app_commands.command(name="pay", description="同志への送金（国庫を通じた富の再分配）")
    async def pay(self, it: discord.Interaction, recipient: discord.Member, amount: int):
        if amount <= 0:
            await it.response.send_message("❌ 報告：0以下の金額は送金できない。やり直せ！", ephemeral=True)
            return

        sender_data = self.ledger.get_user(it.user.id)
        if sender_data["money"] < amount:
            await it.response.send_message(f"❌ 報告：資金が足りない。現在の所持金：{sender_data['money']}", ephemeral=True)
            return

        recipient_data = self.ledger.get_user(recipient.id)
        sender_data["money"] -= amount
        recipient_data["money"] += amount

        self.ledger.save()
        await it.response.send_message(f"💰 送金完了：{it.user.display_name} → {recipient.display_name}（{amount} 資金）")

    # --- /exchange ---
    @app_commands.command(name="exchange", description="貢献度(XP)を資金に変換する")
    async def exchange(self, it: discord.Interaction, amount: int):
        u = self.ledger.get_user(it.user.id)
        if amount <= 0 or u["xp"] < amount:
            await it.response.send_message("❌ 報告：変換可能なXPが不足しているか、数値が不正だ。", ephemeral=True)
            return

        u["xp"] -= amount
        u["money"] += amount
        self.ledger.save()
        await it.response.send_message(f"🔄 変換完了：{amount} XP を {amount} 資金に交換した。労働に励め！")

    # --- /ranking ---
    @app_commands.command(name="ranking", description="労働英雄（XP保有量）ランキング")
    async def ranking(self, it: discord.Interaction):
        # ledgerから全データを取得してソート
        all_users = self.ledger.data
        sorted_users = sorted(all_users.items(), key=lambda x: x[1].get("xp", 0), reverse=True)[:10]

        embed = discord.Embed(title="🏆 労働英雄ランキング (XP)", color=0xffd700)
        for i, (uid, stats) in enumerate(sorted_users, 1):
            user = self.bot.get_user(int(uid))
            name = user.display_name if user else f"未知の同志({uid})"
            embed.add_field(name=f"{i}位: {name}", value=f"{stats['xp']} XP", inline=False)
        
        await it.response.send_message(embed=embed)

    # --- /money_ranking ---
    @app_commands.command(name="money_ranking", description="国家長者番付")
    async def money_ranking(self, it: discord.Interaction):
        all_users = self.ledger.data
        sorted_users = sorted(all_users.items(), key=lambda x: x[1].get("money", 0), reverse=True)[:10]

        embed = discord.Embed(title="💰 国家長者番付", color=0x2ecc71)
        for i, (uid, stats) in enumerate(sorted_users, 1):
            user = self.bot.get_user(int(uid))
            name = user.display_name if user else f"未知の同志({uid})"
            embed.add_field(name=f"{i}位: {name}", value=f"{stats['money']} 資金", inline=False)
        
        await it.response.send_message(embed=embed)

async def setup(bot):
    # ここも後ほどmain.py側で正しくロードする
    pass
