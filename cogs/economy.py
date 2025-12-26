import discord
from discord.ext import commands
from discord import app_commands

class Economy(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="pay", description="指定したユーザーへ資金を送金（振込）します。")
    async def pay(self, it: discord.Interaction, recipient: discord.Member, amount: int):
        if amount <= 0:
            await it.response.send_message("エラー：送金金額は1以上に設定してください。", ephemeral=True)
            return

        sender_data = self.ledger.get_user(it.user.id)
        if sender_data["money"] < amount:
            await it.response.send_message(f"エラー：残高が不足しています。（現在残高：{sender_data['money']:,}）", ephemeral=True)
            return

        recipient_data = self.ledger.get_user(recipient.id)
        sender_data["money"] -= amount
        recipient_data["money"] += amount
        self.ledger.save()

        embed = discord.Embed(title="資金振込完了", color=0x2ecc71)
        embed.description = f"対象アカウントへの送金処理が正常に終了しました。"
        embed.add_field(name="振込元", value=it.user.display_name, inline=True)
        embed.add_field(name="振込先", value=recipient.display_name, inline=True)
        embed.add_field(name="決済金額", value=f"{amount:,.0f} 資金", inline=False)
        embed.set_footer(text="Transaction Management Service")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="exchange", description="蓄積された貢献度(XP)を資金に換算します。")
    async def exchange(self, it: discord.Interaction, amount: int):
        u = self.ledger.get_user(it.user.id)
        if amount <= 0 or u["xp"] < amount:
            await it.response.send_message("エラー：換算可能なXPが不足しているか、数値が不正です。", ephemeral=True)
            return

        u["xp"] -= amount
        u["money"] += amount
        self.ledger.save()

        embed = discord.Embed(title="資産換算処理完了", color=0x3498db)
        embed.description = f"保有資産の振り替えが完了しました。"
        embed.add_field(name="換算したXP", value=f"{amount:,} XP", inline=True)
        embed.add_field(name="加算された資金", value=f"{amount:,} 資金", inline=True)
        embed.set_footer(text="Asset Conversion Module")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="ranking", description="貢献度（XP）の上位10名を表示します。")
    async def ranking(self, it: discord.Interaction):
        all_users = self.ledger.data
        sorted_users = sorted(all_users.items(), key=lambda x: x[1].get("xp", 0), reverse=True)[:10]

        embed = discord.Embed(
            title="📊 貢献度（XP）ランキング",
            description="現在のシステム内におけるアクティブ・スコア上位者です。",
            color=0x34495e
        )
        
        if not sorted_users:
            embed.description = "現在、集計対象データが存在しません。"
        else:
            for i, (uid, stats) in enumerate(sorted_users, 1):
                # ユーザーオブジェクトの取得を試行
                user = it.guild.get_member(int(uid))
                name = user.display_name if user else f"ID: {uid}"
                
                # 順位に応じたインジケータ（上位3名は強調）
                rank_label = f"【第{i}位】" if i <= 3 else f"Rank {i}"
                
                embed.add_field(
                    name=rank_label,
                    value=f"**{name}**\n`{stats['xp']:,} XP`",
                    inline=True
                )

        embed.set_footer(text="System Analytics: Contribution Data")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="money_ranking", description="資産保有量の上位10名を表示します。")
    async def money_ranking(self, it: discord.Interaction):
        all_users = self.ledger.data
        sorted_users = sorted(all_users.items(), key=lambda x: x[1].get("money", 0), reverse=True)[:10]

        embed = discord.Embed(
            title="📈 資産保有量ランキング",
            description="現在のシステム内における総資産額の上位者です。",
            color=0x27ae60
        )
        
        if not sorted_users:
            embed.description = "現在、集計対象データが存在しません。"
        else:
            for i, (uid, stats) in enumerate(sorted_users, 1):
                user = it.guild.get_member(int(uid))
                name = user.display_name if user else f"ID: {uid}"
                
                rank_label = f"【第{i}位】" if i <= 3 else f"Rank {i}"
                
                embed.add_field(
                    name=rank_label,
                    value=f"**{name}**\n`{stats['money']:,} 資金`",
                    inline=True
                )

        embed.set_footer(text="System Analytics: Asset Data")
        await it.response.send_message(embed=embed)

async def setup(bot):
    pass
