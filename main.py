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
        # 起動時のステータスを「退席中(idle)」に、アクティビティを「国家を監視中」に設定
        super().__init__(
            command_prefix="!", 
            intents=intents,
            status=discord.Status.idle,
            activity=discord.Game(name="労働⛏️")
        )

    async def setup_hook(self):
        # cogsフォルダ内の全ファイルをロード
        cog_files = ["utility", "economy", "entertainment", "admin"]
        for file in cog_files:
            try:
                # 動的インポートとインスタンス化
                if file == "utility":
                    from cogs.utility import Utility
                    await self.add_cog(Utility(self, ledger))
                elif file == "economy":
                    from cogs.economy import Economy
                    await self.add_cog(Economy(self, ledger))
                elif file == "entertainment":
                    from cogs.entertainment import Entertainment
                    await self.add_cog(Entertainment(self, ledger))
                elif file == "admin":
                    from cogs.admin import Admin
                    await self.add_cog(Admin(self, ledger))
                
                print(f"[INFO] Cog読み込み成功: {file}")
            except Exception as e:
                print(f"[ERROR] Cog読み込み失敗 {file}: {e}")

        # スラッシュコマンドを同期
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
    
    # 3秒のクールダウン
    if uid not in last_xp_time or (now - last_xp_time[uid]).total_seconds() > 3:
        ledger.add_xp(uid, 2)
        ledger.save()
        last_xp_time[uid] = now

    await bot.process_commands(message)

# --- 起動報告 ---
@bot.event
async def on_ready():
    print(f"🛠️ システム稼働開始：{bot.user.name} (ID: {bot.user.id})")
    print(f"ステータス：{bot.status} / アクティビティ：国家を監視中")
    print("------ 全ての準備が整った。革命は続く。 ------")

# 実行
token = os.getenv("DISCORD_BOT_TOKEN")
bot.run(token)
