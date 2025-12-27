import discord
from discord.ext import commands
import os
import asyncio
import json
import requests

# --- 1. Ledger (帳簿) システム ---
# Gistを利用して、botが再起動してもデータを永続化する仕組み
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
        url = f"https://api.github.com/gists/{self.gist_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            files = response.json().get('files', {})
            content = files.get('ledger.json', {}).get('content', '{}')
            return json.loads(content)
        else:
            print(f"Failed to load ledger: {response.status_code}")
            return {}

    def save(self):
        """Gistにデータを保存する"""
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
            print(f"Failed to save ledger: {response.status_code}")

    def get_user(self, user_id):
        """ユーザーデータを取得、存在しなければ初期化"""
        uid = str(user_id)
        if uid not in self.data:
            self.data[uid] = {
                "money": 100,      # 初期所持金
                "xp": 0,           # 初期経験値
                "level": 1,        # 初期レベル
                "inventory": [],   # アイテム
                "is_studying": False,
                "study_history": {},
                "fishing_inventory": []
            }
        return self.data[uid]

# --- 2. Bot クラスの定義 ---
class Rbm25E(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        # Rb m/25E のプレフィックス設定（スラッシュコマンドメインだが一応設定）
        super().__init__(command_prefix="!", intents=intents)
        
        # 環境変数から設定を読み込み
        self.gist_id = os.getenv("GIST_ID")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.token = os.getenv("DISCORD_TOKEN")
        
        # 帳簿インスタンスの作成
        self.ledger = Ledger(self.gist_id, self.github_token)

    async def setup_hook(self):
        """起動時にCogをロードし、コマンドを同期する"""
        cogs_list = [
            "cogs.admin",
            "cogs.economy",
            "cogs.entertainment",
            "cogs.exchange",
            "cogs.fishing",
            "cogs.gallery",
            "cogs.help",
            "cogs.ping",
            "cogs.ranking",
            "cogs.roulette",
            "cogs.status",
            "cogs.study",
            "cogs.user"
        ]

        for cog in cogs_list:
            try:
                await self.load_extension(cog)
                print(f"✅ Loaded {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")

        # スラッシュコマンドをDiscordサーバーに同期
        await self.tree.sync()
        print("🔄 Slash commands synced.")

    async def on_ready(self):
        """起動完了時の処理"""
        print(f"--- Rb m/25E (Exklusiv Edition) ---")
        print(f"Logged in as: {self.user.name} ({self.user.id})")
        print(f"Status: Online & Stable")
        print(f"-----------------------------------")
        
        # アクティビティの設定
        await self.change_presence(activity=discord.Game(name="/help | Rb m/25E"))

# --- 3. 実行 ---
bot = Rbm25E()

# 各Cogからアクセスできるようにグローバルに公開
ledger_instance = bot.ledger

if __name__ == "__main__":
    asyncio.run(bot.start(bot.token))
