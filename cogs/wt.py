import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

# 国家リストと絵文字の定義
COUNTRIES = {
    "usa": "🇺🇸 USA",
    "germany": "🇩🇪 Germany",
    "ussr": "🇷🇺 USSR",
    "britain": "🇬🇧 Britain",
    "japan": "🇯🇵 Japan",
    "china": "🇨🇳 China",
    "italy": "🇮🇹 Italy",
    "france": "🇫🇷 France",
    "sweden": "🇸🇪 Sweden",
    "israel": "🇮🇱 Israel"
}

class WTView(discord.ui.View):
    """国家選択後の兵器リストを表示するビュー"""
    def __init__(self, vehicles_data):
        super().__init__()
        # 選択メニューを追加（最大25件まで）
        options = []
        for v_id, v_info in list(vehicles_data.items())[:25]:
            name = v_info.get('name', v_id)[:50]
            br = v_info.get('br', '??')
            options.append(discord.SelectOption(label=name, description=f"BR: {br}", value=v_id))
        
        self.add_item(WTVehicleSelect(options))

class WTVehicleSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="兵器を選択してください...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # 選択された兵器の個別APIを叩く
        v_id = self.values[0]
        # ※ここでは簡易化のためIDから情報を再構築するか、再度APIを叩く処理を入れる
        await interaction.followup.send(f"📄 **{v_id}** の詳細データを照会中...（ここにスペックを表示）")

class WarThunder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://www.wtvehiclesapi.repository.guru/api/vehicles/"

    @app_commands.command(name="wt", description="国家別カタログを開きます")
    async def wt(self, interaction: discord.Interaction):
        # 国家選択用プルダウンを作成
        view = discord.ui.View()
        select = discord.ui.Select(placeholder="国家を選択してください...")
        
        for code, name in COUNTRIES.items():
            select.add_item(discord.SelectOption(label=name, value=code))
            
        async def country_callback(it: discord.Interaction):
            await it.response.defer()
            country_code = select.values[0]
            
            # その国家の全兵器を取得（例：tanksカテゴリ）
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}tanks") as resp:
                    all_tanks = await resp.json()
                    # 国家でフィルタリング
                    filtered = {k: v for k, v in all_tanks.items() if v.get('country') == country_code}
                    
                    if not filtered:
                        return await it.followup.send(f"❌ {country_code} のデータが見つかりませんでした。")
                    
                    # 兵器選択用の新しいUIを表示
                    await it.followup.send(f"📂 {COUNTRIES[country_code]} の陸上兵器リスト:", view=WTView(filtered))

        select.callback = country_callback
        view.add_item(select)
        await interaction.response.send_message("🛠️ **War Thunder 兵器カタログ**へようこそ。調査対象の国家を選択してください。", view=view)

async def setup(bot):
    await bot.add_cog(WarThunder(bot))
