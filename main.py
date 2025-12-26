import discord
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta, timezone
from ledger import Ledger

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GIST_ID = os.getenv("GIST_ID")
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")
# 一旦、特定のサーバーへの強制同期をやめるため、None にするかコメントアウト推奨
GUILD_ID = 123456789012345678  # あなたのサーバーID

JST = timezone(timedelta(hours=9), 'JST')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class Rb_m25_Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        self.start_time = datetime.now(JST)
        self.ledger = Ledger(GIST_ID, GITHUB_TOKEN) if GIST_ID and GITHUB_TOKEN else None

    async def setup_hook(self):
        print("--- [CLEANUP MODE] ---")
        
        # 読み込むリスト（ここに書いたファイルが cogs/ フォルダに実在する必要があります）
        cogs_list = [
            "cogs.status", "cogs.economy", "cogs.admin",
            "cogs.entertainment", "cogs.roulette", "cogs.user",
            "cogs.ping", "cogs.help", "cogs.exchange", "cogs.study"
        ]
        
        for cog in cogs_list:
            try:
                await self.load_extension(cog)
                print(f"✅ Loaded: {cog}")
            except Exception as e:
                # ここでエラーが出る場合、ファイルがないか、中身にミスがあります
                print(f"❌ Failed: {cog} | {e}")

        # --- 二重表示を直すためのリセット処理 ---
        if GUILD_ID:
            target_guild = discord.Object(id=GUILD_ID)
            print(f"♻️ サーバー専用コマンド ({GUILD_ID}) を完全に削除してグローバルに一本化します...")
            self.tree.clear_commands(guild=target_guild)
            await self.tree.sync(guild=target_guild)

        # 全体（グローバル）同期のみを実行
        await self.tree.sync()
        print("🌎 グローバル同期を完了。反映まで最大1時間かかる場合があります。")
        
        self.update_status.start()

    @tasks.loop(seconds=10)
    async def update_status(self):
        if not self.is_ready(): return
        now = datetime.now(JST)
        uptime = now - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        status_text = f"Up: {hours}h {minutes}m | {now.strftime('%H:%M')} JST"
        await self.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.watching, name=status_text))

bot = Rb_m25_Bot()
@bot.event
async def on_ready():
    print(f"--- Rb m/25 Online ---")

if TOKEN:
    bot.run(TOKEN)
