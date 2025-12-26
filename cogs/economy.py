import discord
from discord.ext import commands
from discord import app_commands

class Economy(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    # --- /pay ---
    @app_commands.command(name="pay", description="指定したユーザーに資金を送金します。")
    async def pay(self, it: discord.Interaction, recipient: discord.Member, amount: int):
        if amount <= 0:
            await it.response.send_message("エラー：1以上の数値を入力してください。", ephemeral=True)
            return

        sender_data = self.ledger.get_user(it.user.id)
        if sender_data["money"] < amount:
            await it.response.send_message(f"エラー：残高が不足しています。（現在残高：{sender_data['money']}）", ephemeral=True)
            return

        recipient_data = self.ledger.get_user(recipient.id)
        sender_data["money"] -= amount
        recipient_data["money"] += amount
        self.ledger.save()

        embed = discord.Embed(title="資金振込完了", color=0x2ecc71)
        embed.description = f"{it.user.display_name} 様から {recipient.display_name} 様への送金処理が正常に完了いたしました。"
        embed.add_field(name="決済金額", value=f"{amount:,.0f} 資金", inline=True)
        embed.set_footer(text="Transaction Management Service")
        await it.response.send_message(embed=embed)

    # --- /exchange ---
    @app_commands.command(name="exchange", description="蓄積されたXPを資金に換算します。")
    async def exchange(self, it: discord.Interaction, amount: int):
        u = self.ledger.get_user(it.user.id)
        if amount <= 0 or u["xp"] < amount:
            await it.response.send_message("エラー：入力されたXPが不足しているか、不正な数値です。", ephemeral=True)
            return

        u["xp"] -= amount
        u["money"] += amount
        self.ledger.save()

        embed = discord.Embed(title="資産換算処理完了", color=0x3498db)
        embed.description = f"保有されている **{amount} XP** を **{amount} 資金** へ振り替えました。"
        embed.set_footer(text="Asset Conversion Module")
        await it.response.send_message(embed=embed)

    # --- /ranking ---
    @app_commands.command(name="ranking", description="XP保有量のランキングを表示します。")
    async def ranking(self, it: discord.Interaction):
        all_users = self.ledger.data
        sorted_users = sorted(all_users.items(), key=lambda x: x[1].get("xp", 0), reverse=True)[:10]

        embed = discord.Embed(title="貢献度（XP）ランキング上位", color=0x95a5a6)
        
        ranking_text = ""
        for i, (uid, stats) in enumerate(sorted_users, 1):
            symbol = "●" # 装飾を控えめに
            ranking_text += f"{i:2d}. <@{uid}> ― `{stats['xp']:,}` XP\n"

        embed.description = f"```{ranking_text if ranking_text else 'データなし'}```"
        embed.set_footer(text="System Statistics Data")
        await it.response.send_message(embed=embed)

    # --- /money_ranking ---
    @app_commands.command(name="money_ranking", description="資金保有量のランキングを表示します。")
    async def money_ranking(self, it: discord.Interaction):
        all_users = self.ledger.data
        sorted_users = sorted(all_users.items(), key=lambda x: x[1].get("money", 0), reverse=True)[:10]

        embed = discord.Embed(title="資産保有量ランキング上位", color=0x27ae60)
        
        ranking_text = ""
        for i, (uid, stats) in enumerate(sorted_users, 1):
            ranking_text += f"{i:2d}. <@{uid}> ― `{stats['money']:,}` 資金\n"

        embed.description = f"```{ranking_text if ranking_text else 'データなし'}```"
        embed.set_footer(text="Asset Analysis Data")
        await it.response.send_message(embed=embed)

async def setup(bot):
    pass
