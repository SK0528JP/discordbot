import discord
from discord.ext import commands
import os
import asyncio
from ledger import Ledger

# 1. データの心臓部を起動
ledger = Ledger()

# 2. ボットの基本設定
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # cogsフォルダ内の全ファイルをロード
        cog_files = ["utility", "economy", "entertainment", "admin"]
        for file in cog_files:
            try:
                # ここで各Cogを読み込み、ledgerインスタンスを共有させる
                from cogs.utility import Utility
                from cogs.economy import Economy
                from cogs.entertainment import Entertainment
                from cogs.admin import Admin
                
                # 手動マッピング（確実性を期すため）
                cogs_map = {
                    "utility": Utility,
                    "economy": Economy,
                    "entertainment": Entertainment,
                    "admin": Admin
                }
                
                cog_class = cogs_map[file]
                await self.add_cog(cog_class(self, ledger))
                print(f"[INFO] Cog読み込み成功: {file}")
            except Exception as e:
                print(f"[ERROR] Cog読み込み失敗 {file}: {e}")

        # スラッシュコマンドをDiscordサーバーへ同期
        await self.tree.sync()
        print("[INFO] スラッシュコマンド同期完了")

bot = MyBot()

# --- 労働監視（XP自動加算システム） ---
last_xp_time = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    now = discord.utils.utcnow()
    uid = message.author.id
    
    # 3秒のクールダウン（連投によるXP不正取得を防止）
    if uid not in last_xp_time or (now - last_xp_time[uid]).total_seconds() > 3:
        ledger.add_xp(uid, 2)
        ledger.save()  # 労働を即座に記録
        last_xp_time[uid] = now

    await bot.process_commands(message)

# --- 起動報告 ---
@bot.event
async def on_ready():
    print(f"🛠️ システム稼働開始：{bot.user.name} (ID: {bot.user.id})")
    print("------ 国家の安寧は守られた ------")

# 実行
token = os.getenv("DISCORD_BOT_TOKEN")
bot.run(token)
