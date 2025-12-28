import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio

COUNTRIES = {
    "usa": "🇺🇸 USA", "germany": "🇩🇪 Germany", "ussr": "🇷🇺 USSR",
    "britain": "🇬🇧 Britain", "japan": "🇯🇵 Japan", "china": "🇨🇳 China",
    "italy": "🇮🇹 Italy", "france": "🇫🇷 France", "sweden": "🇸🇪 Sweden", "israel": "🇮🇱 Israel"
}
CATEGORIES = {
    "tanks": "🚜 陸上兵器", "planes": "✈️ 航空機", 
    "ships": "🚢 艦艇", "helicopters": "🚁 ヘリコプター"
}

class WTVehicleSelect(discord.ui.Select):
    def __init__(self, options, category):
        super().__init__(placeholder="調査する兵器を選択してください...", options=options)
        self.category = category

    async def callback(self, interaction: discord.Interaction):
        # 3秒ルール回避のため即座に応答
        await interaction.response.defer()
        
        v_id = self.values[0]
        # 重い /all ではなく、カテゴリ別エンドポイントから取得
        url = f"https://www.wtvehiclesapi.repository.guru/api/vehicles/{self.category}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        res = data.get(v_id)
                        if res:
                            embed = discord.Embed(
                                title=f"📊 兵器データ: {res.get('name', v_id)}",
                                color=discord.Color.gold()
                            )
                            embed.add_field(name="国家", value=res.get('country', '不明').upper(), inline=True)
                            embed.add_field(name="BR", value=res.get('br', '不明'), inline=True)
                            if 'image_url' in res:
                                embed.set_image(url=res['image_url'])
                            return await interaction.followup.send(embed=embed)
        except Exception as e:
            return await interaction.followup.send(f"⚠️ 詳細取得エラー: サーバーが混雑しています。")

class WarThunder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_base = "https://www.wtvehiclesapi.repository.guru/api/vehicles"

    @app_commands.command(name="wt", description="War Thunder兵器カタログ（高速版）")
    async def wt(self, interaction: discord.Interaction):
        view = discord.ui.View(timeout=60)
        select = discord.ui.Select(placeholder="国家を選択してください...")
        for code, label in COUNTRIES.items():
            select.add_item(discord.SelectOption(label=label, value=code))

        async def country_callback(it: discord.Interaction):
            # 選択された国家を一時保存して次のメニューへ
            await it.response.defer(ephemeral=True)
            country_code = select.values[0]
            
            cat_view = discord.ui.View(timeout=60)
            for cat_id, cat_label in CATEGORIES.items():
                button = discord.ui.Button(label=cat_label, custom_id=f"{country_code}_{cat_id}")
                
                async def btn_callback(btn_it: discord.Interaction):
                    await btn_it.response.defer(ephemeral=True)
                    c_code, c_id = btn_it.data['custom_id'].split('_')
                    
                    try:
                        async with aiohttp.ClientSession() as session:
                            # 巨大な all は使わず、カテゴリ単位(tanks等)で取得
                            async with session.get(f"{self.api_base}/{c_id}", timeout=5) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    # 国家フィルタリング
                                    filtered = {k: v for k, v in data.items() if v.get('country') == c_code}
                                    
                                    if not filtered:
                                        return await btn_it.followup.send("❌ 指定国家のデータがこのカテゴリにありません。")
                                    
                                    # セレクトメニュー作成
                                    options = []
                                    for v_id, v_info in list(filtered.items())[:25]:
                                        name = v_info.get('name', v_id)[:50]
                                        options.append(discord.SelectOption(label=name, value=v_id))
                                    
                                    final_view = discord.ui.View()
                                    final_view.add_item(WTVehicleSelect(options, c_id))
                                    await btn_it.followup.send(f"📂 {COUNTRIES[c_code]} リストを表示します:", view=final_view)
                                else:
                                    await btn_it.followup.send("⚠️ APIサーバーが応答しませんでした。")
                    except asyncio.TimeoutError:
                        await btn_it.followup.send("⏳ 接続タイムアウト。もう一度お試しください。")

                button.callback = btn_callback
                cat_view.add_item(button)
            
            await it.followup.send(f"📍 国家: {COUNTRIES[country_code]}。カテゴリを選択:", view=cat_view)

        select.callback = country_callback
        view.add_item(select)
        await interaction.response.send_message("🛠️ **Rb m/25E 兵器データベース**", view=view)

async def setup(bot):
    await bot.add_cog(WarThunder(bot))
