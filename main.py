import discord
from discord.ext import commands, tasks
import os
import asyncio
from datetime import datetime, timedelta, timezone
from ledger import Ledger

# --- 基本設定 ---
# GitHub Secretsの名前と一致させています
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GIST_ID = os.getenv("GIST_ID")
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")

# JST (日本標準時) の定義
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
        # 起動時刻をJSTで記録
        self.start_time = datetime.now(JST)

    async def setup_hook(self):
        # 専門ユニット(Cogs)の登録
        cogs_list = [
            "cogs.status", "cogs.economy", "cogs.admin",
            "cogs.entertainment", "cogs.roulette", "cogs.user",
            "cogs.ping", "cogs.help", "cogs.exchange"
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
        
        # ステータス更新ループを開始
        self.update_status.start()

    # 10秒ごとにステータスを更新するタスク
    @tasks.loop(seconds=10)
    async def update_status(self):
        if not self.is_ready():
            return

        # 1. レイテンシの取得
        latency = round(self.latency * 1000)
        
        # 2. 稼働時間の計算
        now = datetime.now(JST)
        uptime = now - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        
        # 3. 曜日の日本語マップ
        wd_list = ["月", "火", "水", "木", "金", "土", "日"]
        weekday_str = wd_list[now.weekday()]
        
        # 4. 現在時刻のフォーマット (秒なし・曜日あり)
        time_str = now.strftime(f"%Y/%m/%d({weekday_str}) %H:%M")
        
        # アクティビティ文字列の構築
        status_text = f"Lat: {latency}ms | Up: {hours}h {minutes}m | {time_str} JST"
        
        # 退席中ステータスで「～を視聴中」として表示
        await self.change_presence(
            status=discord.Status.idle,
            activity=discord.Activity(
                type=discord.ActivityType.watching, 
                name=status_text
            )
        )

bot = Rb_m25_Bot()

# Ledgerの初期化
if GIST_ID and GITHUB_TOKEN:
    ledger_instance = Ledger(GIST_ID, GITHUB_TOKEN)
else:
    print("⚠️ Warning: GIST_ID or MY_GITHUB_TOKEN is missing.")
    ledger_instance = None

@bot.event
async def on_ready():
    print(f"--- Rb m/25 System Online ---")
    print(f"Node Name: {bot.user.name}")
    print(f"Status   : IDLE (JST Monitoring Mode)")
    print(f"-----------------------------")

@bot.event
async def on_message(message):
    if message.author.bot or ledger_instance is None:
        return
    
    # 貢献度(XP)の蓄積
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
