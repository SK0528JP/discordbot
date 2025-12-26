import discord
from discord.ext import commands
import os
import asyncio
from ledger import Ledger

# --- 基本設定 ---
# GitHub Secrets で設定されている名前に合わせて取得
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GIST_ID = os.getenv("GIST_ID")
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")

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

    async def setup_hook(self):
        # 分割された専門ユニット(Cogs)の登録
        cogs_list = [
            "cogs.status",
            "cogs.economy",
            "cogs.admin",
            "cogs.entertainment",
            "cogs.roulette",
            "cogs.user",
            "cogs.ping",
            "cogs.help",
            "cogs.exchange"
        ]
        for cog in cogs_list:
            try:
                await self.load_extension(cog)
                print(f"✅ Module Loaded: {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")

        # スラッシュコマンドの同期
        await self.tree.sync()
        print("🛰️ Command Tree Synced.")

bot = Rb_m25_Bot()

# Ledgerの初期化 (Secrets から取得したトークンを渡す)
if GIST_ID and GITHUB_TOKEN:
    ledger_instance = Ledger(GIST_ID, GITHUB_TOKEN)
else:
    print("⚠️ Warning: GIST_ID or MY_GITHUB_TOKEN is missing.")
    ledger_instance = None

@bot.event
async def on_ready():
    # ステータスを「退席中 (idle)」に設定
    await bot.change_presence(
        status=discord.Status.idle, 
        activity=discord.Game(name="Rb m/25 System Monitoring")
    )
    
    print(f"--- Rb m/25 System Online ---")
    print(f"Node Name: {bot.user.name}")
    print(f"Node ID  : {bot.user.id}")
    print(f"Status   : IDLE (Monitoring Mode)")
    print(f"-----------------------------")

@bot.event
async def on_message(message):
    if message.author.bot or ledger_instance is None:
        return
    
    # メッセージ送信による貢献度(XP)の蓄積
    u = ledger_instance.get_user(message.author.id)
    u["xp"] += 1
    
    # 30メッセージごとに自動保存
    if u["xp"] % 30 == 0:
        ledger_instance.save()
    
    await bot.process_commands(message)

# 実行
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Error: DISCORD_BOT_TOKEN is not set.")
