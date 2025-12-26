import discord
from discord.ext import commands
from discord import app_commands

class Exchange(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger
        # 変換レート設定: 10 XP を 1 cr に変換
        self.rate = 0.1

    @app_commands.command(name="exchange", description="蓄積した貢献度(XP)を資産(Credits)に換金します")
    @app_commands.describe(amount="換金したいXPの量を入力してください")
    async def exchange(self, it: discord.Interaction, amount: int):
        """
        XPを消費してMoneyを生成する中央銀行ユニット。
        """
        if amount <= 0:
            await it.response.send_message("❌ 1 XP以上を指定してください。", ephemeral=True)
            return

        u = self.ledger.get_user(it.user.id)
        current_xp = u.get("xp", 0)

        if current_xp < amount:
            await it.response.send_message(
                f"❌ XPが不足しています。\n保有: `{current_xp:,} XP` / 入力: `{amount:,} XP`", 
                ephemeral=True
            )
            return

        # 換金計算
        receive_money = int(amount * self.rate)
        
        if receive_money <= 0:
            await it.response.send_message(
                f"❌ 換金額が少なすぎます。現在のレートでは `{int(1/self.rate)} XP` 以上必要です。", 
                ephemeral=True
            )
            return

        # データの更新
        u["xp"] -= amount
        u["money"] += receive_money
        self.ledger.save()

        embed = discord.Embed(
            title="💎 資産換金完了",
            description=f"貢献度を資産に正常に変換しました。",
            color=0x10b981 # Emerald
        )
        embed.add_field(name="📉 消費した貢献度", value=f"`{amount:,} XP`", inline=True)
        embed.add_field(name="📈 獲得した資産", value=f"`{receive_money:,} cr`", inline=True)
        embed.add_field(name="💰 現在の総資産", value=f"`{u['money']:,} cr`", inline=False)
        
        embed.set_footer(text=f"Rb m/25 Exchange Rate: 10 XP = 1 cr")
        
        await it.response.send_message(embed=embed)

async def setup(bot):
    from __main__ import ledger_instance
    await bot.add_cog(Exchange(bot, ledger_instance))
