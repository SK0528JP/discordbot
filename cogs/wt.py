import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

# 定数定義
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
    """兵器リストのプルダウン"""
    def __init__(self, options):
        super().__init__(placeholder="調査する兵器を選択してください...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        v_id = self.values[0]
        # 選択された兵器の詳細を取得
        url = f"https://www.wtvehiclesapi.repository.guru/api/vehicles/all" # 簡易化のため全リストから抽出
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    res = data.get(v_id)
                    if res:
                        embed = discord.Embed(
                            title=f"📊 兵器データ: {res.get('name', v_id)}",
                            description=f"ID: `{v_id}`",
                            color=discord.Color.gold()
                        )
                        embed.add_field(name="国家", value=res.get('country', '不明').upper(), inline=True)
                        embed.add_field(name="ランク", value=res.get('rank', '不明'), inline=True)
                        embed.add_field(name="BR", value=res.get('br', '不明'), inline=True)
                        if 'image_url' in res:
                            embed.set_image(url=res['image_url'])
                        embed.set_footer(text="Rb m/25E 戦術データライブラリ")
                        return await interaction.followup.send(embed=embed)
        await interaction.followup.send("❌ データの取得に失敗しました。")

class WTCategoryView(discord.ui.View):
    """カテゴリ選択後の兵器リストを表示するView"""
    def __init__(self, vehicles_dict):
        super().__init__(timeout=60)
        options = []
        # 最大25件までの制限があるためスライス
        for v_id, v_info in list(vehicles_dict.items())[:25]:
            name = v_info.get('name', v_id)[:50]
            br = v_info.get('br', '??')
            options.append(discord.SelectOption(label=name, description=f"BR: {br}", value=v_id))
        
        if options:
            self.add_item(WTVehicleSelect(options))

class WarThunder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_base = "https://www.wtvehiclesapi.repository.guru/api/vehicles"

    @app_commands.command(name="wt", description="War Thunder兵器カタログを閲覧します")
    async def wt(self, interaction: discord.Interaction):
        """最初の国家選択メッセージ"""
        view = discord.ui.View(timeout=60)
        select = discord.ui.Select(placeholder="調査対象の国家を選択してください...")
        
        for code, label in COUNTRIES.items():
            select.add_item(discord.SelectOption(label=label, value=code))

        async def country_callback(it: discord.Interaction):
            # 2段階目：カテゴリ選択（陸・空・海）
            country_code = select.values[0]
            cat_view = discord.ui.View(timeout=60)
            
            for cat_id, cat_label in CATEGORIES.items():
                # ボタン形式でカテゴリを選択
                button = discord.ui.Button(label=cat_label, custom_id=f"{country_code}_{cat_id}")
                
                async def btn_callback(btn_it: discord.Interaction):
                    await btn_it.response.defer()
                    c_code, c_id = btn_it.data['custom_id'].split('_')
                    
                    # APIからデータを取得
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{self.api_base}/{c_id}") as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                # 指定国家の兵器だけ抽出
                                filtered = {k: v for k, v in data.items() if v.get('country') == c_code}
                                if not filtered:
                                    return await btn_it.followup.send(f"❌ {COUNTRIES[c_code]} の {CATEGORIES[c_id]} データがありません。")
                                
                                await btn_it.followup.send(f"📂 {COUNTRIES[c_code]} {CATEGORIES[c_id]} リスト:", view=WTCategoryView(filtered))
                            else:
                                await btn_it.followup.send("⚠️ データ取得エラーが発生しました。")

                button.callback = btn_callback
                cat_view.add_item(button)
            
            await it.response.send_message(f"📍 {COUNTRIES[country_code]} が選択されました。カテゴリを選んでください。", view=cat_view, ephemeral=True)

        select.callback = country_callback
        view.add_item(select)
        await interaction.response.send_message("🛠️ **Rb m/25E 戦術データベース**へようこそ。", view=view)

async def setup(bot):
    await bot.add_cog(WarThunder(bot))
