import discord
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta, timezone
from ledger import Ledger

# --- 環境設定 ---
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GIST_ID = os.getenv("GIST_ID")
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")
JST = timezone(timedelta(hours=9), 'JST')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class Rb_m25_Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        self.start_time = datetime.now(JST)
        # Ledgerの初期化（他のCogから self.bot.ledger でアクセス可能にする）
        self.ledger = Ledger(GIST_ID, GITHUB_TOKEN) if GIST_ID and GITHUB_TOKEN else None

    async def setup_hook(self):
        # study を含むモジュールリスト
        cogs_list = [
            "cogs.status", "cogs.economy", "cogs.admin",
            "cogs.entertainment", "cogs.roulette", "cogs.user",
            "cogs.ping", "cogs.help", "cogs.exchange", "cogs.study"
        ]
        for cog in cogs_list:
            try:
                await self.load_extension(cog)
                print(f"✅ Module Loaded: {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")

        await self.tree.sync()
        self.update_status.start()

    @tasks.loop(seconds=10)
    async def update_status(self):
        if not self.is_ready(): return
        latency = round(self.latency * 1000)
        now = datetime.now(JST)
        uptime = now - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        
        wd_list = ["月", "火", "水", "木", "金", "土", "日"]
        time_str = now.strftime(f"%Y/%m/%d({wd_list[now.weekday()]}) %H:%M")
        
        status_text = f"Lat: {latency}ms | Up: {hours}h {minutes}m | {time_str} JST"
        await self.change_presence(
            status=discord.Status.idle,
            activity=discord.Activity(type=discord.ActivityType.watching, name=status_text)
        )

bot = Rb_m25_Bot()

@bot.event
async def on_ready():
    print(f"--- Rb m/25 System Online ---")
    print(f"Target Server: 同志たち")
    print(f"-----------------------------")

@bot.event
async def on_message(message):
    if message.author.bot or bot.ledger is None: return
    u = bot.ledger.get_user(message.author.id)
    u["xp"] += 1
    if u["xp"] % 30 == 0: bot.ledger.save()
    await bot.process_commands(message)

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Error: DISCORD_BOT_TOKEN is missing.")
