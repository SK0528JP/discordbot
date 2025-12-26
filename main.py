import discord
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta, timezone
from ledger import Ledger

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GIST_ID = os.getenv("GIST_ID")
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")
# 403エラーを避けるため、一旦Noneにします。
# コマンドを即時反映させたい場合は、Botの権限を確認してからIDを入れてください。
GUILD_ID = None 

JST = timezone(timedelta(hours=9), 'JST')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class Rb_m25_Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        self.start_time = datetime.now(JST)
        # 既存Cogが「from __main__ import ledger_instance」としている場合に対応
        self.ledger = Ledger(GIST_ID, GITHUB_TOKEN) if GIST_ID and GITHUB_TOKEN else None
        global ledger_instance
        ledger_instance = self.ledger

    async def setup_hook(self):
        print("--- [RECOVERY MODE] ---")
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
                print(f"❌ Failed: {cog} | {e}")

        # 403 Forbidden対策：権限がない場合はスキップするように保護
        try:
            if GUILD_ID:
                target_guild = discord.Object(id=GUILD_ID)
                self.tree.copy_global_to(guild=target_guild)
                await self.tree.sync(guild=target_guild)
                print(f"🛰️ Guild {GUILD_ID} synced.")
            else:
                await self.tree.sync()
                print("🌎 Global sync requested.")
        except discord.errors.Forbidden:
            print("⚠️ 権限不足によりギルド同期をスキップしました。Botを招待し直すか権限を確認してください。")
            await self.tree.sync() # グローバル同期を試行

        self.update_status.start()

    @tasks.loop(seconds=10)
    async def update_status(self):
        if not self.is_ready(): return
        now = datetime.now(JST)
        status_text = f"Rb m/25 | {now.strftime('%H:%M')} JST"
        await self.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.watching, name=status_text))

# 他のCogが import できるようにグローバル変数として定義
ledger_instance = None
bot = Rb_m25_Bot()

if TOKEN:
    bot.run(TOKEN)
