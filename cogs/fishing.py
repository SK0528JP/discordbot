import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
from datetime import datetime

class Fishing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 獲物データ：名前, 基本価格, サイズ範囲(min, max), レア度
        self.FISH_DATA = [
            {"name": "アジ", "base_price": 50, "size_range": (15, 30), "rarity": "N"},
            {"name": "イワシ", "base_price": 30, "size_range": (10, 25), "rarity": "N"},
            {"name": "タイ", "base_price": 200, "size_range": (30, 80), "rarity": "R"},
            {"name": "マグロ", "base_price": 1000, "size_range": (100, 300), "rarity": "SR"},
            {"name": "リュウグウノツカイ", "base_price": 5000, "size_range": (300, 600), "rarity": "SSR"},
            {"name": "長靴", "base_price": 5, "size_range": (20, 30), "rarity": "ゴミ"},
            {"name": "空き缶", "base_price": 1, "size_range": (5, 10), "rarity": "ゴミ"},
        ]

    @app_commands.command(name="fishing", description="釣りをします。何が釣れるかな？")
    async def fishing(self, interaction: discord.Interaction):
        await interaction.response.send_message("🎣 釣り糸を垂らしました。アタリを待っています...")
        
        # 3〜5秒のランダムな待機時間（演出）
        await asyncio.sleep(random.randint(3, 5))

        # 獲物の抽選
        fish_base = random.choices(
            self.FISH_DATA, 
            weights=[40, 40, 15, 4, 0.5, 10, 10], # 出現確率の重み
            k=1
        )[0]

        size = round(random.uniform(fish_base["size_range"][0], fish_base["size_range"][1]), 1)
        # サイズが大きいほど価格が上がる（基本価格 * サイズ比）
        price = int(fish_base["base_price"] * (size / fish_base["size_range"][0]))

        # ユーザーデータの取得と保存
        user_data = self.bot.ledger.get_user(interaction.user.id)
        if "fishing_inventory" not in user_data:
            user_data["fishing_inventory"] = []
        
        new_item = {
            "name": fish_base["name"],
            "size": size,
            "price": price,
            "rarity": fish_base["rarity"],
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        user_data["fishing_inventory"].append(new_item)
        self.bot.ledger.save()

        # 結果表示
        color = discord.Color.blue()
        if fish_base["rarity"] == "SR": color = discord.Color.purple()
        if fish_base["rarity"] == "SSR": color = discord.Color.gold()
        if fish_base["rarity"] == "ゴミ": color = discord.Color.dark_gray()

        embed = discord.Embed(title="🐟 釣果報告！", color=color)
        embed.add_field(name="名前", value=f"**{fish_base['name']}**", inline=True)
        embed.add_field(name="サイズ", value=f"{size} cm", inline=True)
        embed.add_field(name="レア度", value=fish_base["rarity"], inline=True)
        embed.set_footer(text="インベントリに追加されました。/fishing_inventory で確認できます。")
        
        await interaction.edit_original_response(content=None, embed=embed)

    @app_commands.command(name="fishing_inventory", description="自分の釣った獲物一覧を表示します")
    async def fishing_inventory(self, interaction: discord.Interaction):
        user_data = self.bot.ledger.get_user(interaction.user.id)
        inventory = user_data.get("fishing_inventory", [])

        if not inventory:
            await interaction.response.send_message("🪣 バケツは空っぽだ。釣りにいこう！", ephemeral=True)
            return

        embed = discord.Embed(title=f"🪣 {interaction.user.display_name} の生け簀", color=discord.Color.blue())
        
        desc = ""
        for i, item in enumerate(inventory):
            desc += f"`{i}`: **{item['name']}** ({item['size']}cm) - {item['price']}円\n"
            # 1つのEmbedに載せすぎるとエラーになるので15件でカット
            if i >= 14:
                desc += "...(以降は売却して整理してください)"
                break
        
        embed.description = desc
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="fishing_sale", description="番号を指定して獲物を売却します")
    @app_commands.describe(index="売却する魚の番号（inventoryで確認可能）")
    async def fishing_sale(self, interaction: discord.Interaction, index: int):
        user_data = self.bot.ledger.get_user(interaction.user.id)
        inventory = user_data.get("fishing_inventory", [])

        if index < 0 or index >= len(inventory):
            await interaction.response.send_message("❌ その番号の獲物は見当たらないぞ。", ephemeral=True)
            return

        # 獲物の取り出し
        item = inventory.pop(index)
        sale_price = item["price"]

        # 通貨へ加算（ledgerのmoney変数を使用）
        user_data["money"] = user_data.get("money", 0) + sale_price
        self.bot.ledger.save()

        await interaction.response.send_message(
            f"💰 **{item['name']}** ({item['size']}cm) を売却した！\n"
            f"**{sale_price}円** を手に入れたぞ。（現在の所持金: {user_data['money']}円）"
        )

async def setup(bot):
    await bot.add_cog(Fishing(bot))
