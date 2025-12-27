import discord
from discord.ext import commands
import os
import asyncio
import json
import requests

# --- 1. Ledger (帳簿) システム ---
class Ledger:
    def __init__(self, gist_id, github_token):
        self.gist_id = gist_id
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.data = self._load()

    def _load(self):
        """Gistからデータを読み込む"""
        if not self.gist_id or "token None" in self.headers["Authorization"]:
            print("❌ Gist ID または GitHub Token が設定されていません。")
            return {}
            
        url = f"https://api.github.com/gists/{self.gist_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            files = response.json().get('files', {})
            content = files.get('ledger.json', {}).get('content', '{}')
            return json.loads(content)
        else:
            print(f"❌ Failed to load ledger: {response.status_code}")
            return {}

    def save(self):
        """Gistにデータを保存する"""
        if not self.gist_id: return
        url = f"https://api.github.com/gists/{self.gist_id}"
        payload = {
            "files": {
                "ledger.json": {
                    "content": json.dumps(self.data, indent=4)
                }
            }
        }
        response = requests.patch(url, headers=self.headers, json=payload)
        if response.status_code != 200:
            print(f"❌ Failed to save ledger: {response.status_code}")

    def get_user(self, user_id):
        uid = str(user_id)
        if uid not in self.data:
            self.data[uid] = {
                "money": 100,
                "xp": 0,
                "level": 1,
                "inventory": [],
                "is_studying": False,
                "study_history": {},
                "fishing_inventory": []
            }
        return self.data[uid]

# --- 2. Bot クラスの定義 ---
class Rbm25E(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)
        
        # 司令官指定の環境変数名に変更
        self.gist_id = os.getenv("GIST_ID")
        self.github_token = os.getenv("MY_GITHUB_TOKEN")
        self.token = os.getenv("DISCORD_BOT_TOKEN")
        
        # 帳簿インスタンスの作成
        self.ledger = Ledger(self.gist_id, self.github_token)

    async def setup_hook(self):
        """起動時にCogをロード"""
        cogs_list = [
            "cogs.admin", "cogs.economy", "cogs.entertainment",
            "cogs.exchange", "cogs.fishing", "cogs.gallery",
            "cogs.help", "cogs.ping", "cogs.ranking",
            "cogs.roulette", "cogs.status", "cogs.study", "cogs.user"
        ]

        for cog in cogs_list:
            try:
                await self.load_extension(cog)
                print(f"✅ Loaded {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")

        await self.tree.sync()
        print("🔄 Slash commands synced.")

    async def on_ready(self):
        print(f"--- Rb m/25E (Exklusiv Edition) ---")
        print(f"Logged in as: {self.user.name}")
        print(f"Status: Online & Stable")
        print(f"-----------------------------------")
        
        # ステータス設定
        await self.change_presence(
            status=discord.Status.idle, 
            activity=discord.Game(name="/help | Rb m/25E")
        )

# --- 3. 実行 ---
bot = Rbm25E()

async def main():
    async with bot:
        if not bot.token:
            print("❌ DISCORD_BOT_TOKEN が環境変数に見つかりません。")
            return
        await bot.start(bot.token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
