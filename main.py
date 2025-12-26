import discord
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta, timezone
from ledger import Ledger

# --- 環境設定 ---
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GIST_ID = os.getenv("GIST_ID")
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")
# サーバーIDをここに入力（スラッシュコマンド即時反映用）
GUILD_ID = 1062900513017962576  # ← 【ここを自分のサーバーIDに書き換え】

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
        # Ledgerの初期化
        self.ledger = Ledger(GIST_ID, GITHUB_TOKEN) if GIST_ID and GITHUB_TOKEN else None

    async def setup_hook(self):
        # 読み込むCogのリスト
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

        # --- 強制同期処理 ---
        if GUILD_ID:
            target_guild = discord.Object(id=GUILD_ID)
            # 現在読み込まれている全コマンドをサーバー専用にコピー
            self.tree.copy_global_to(guild=target_guild)
            # サーバーに対して即時同期
            await self.tree.sync(guild=target_guild)
            print(f"🛰️ Command Tree Synced to Guild: {GUILD_ID}")
        
        # グローバル（全体）同期もバックグラウンドで実行
        await self.tree.sync()
        
        # ステータス更新ループ開始
        self.update_status.start()

    @tasks.loop(seconds=10)
    async def update_status(self):
        if not self.is_ready(): return
        
        latency = round(self.latency * 1000)
        now = datetime.now(JST)
        uptime = now - self.start_time
        
        # 稼働時間の計算
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
    print(f"Logged in as: {bot.user.name}")
    print(f"Time: {datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"-----------------------------")

@bot.event
async def on_message(message):
    # Botのメッセージは無視
    if message.author.bot:
        return
    
    # メッセージごとにXP加算（Ledgerが有効な場合）
    if bot.ledger:
        u = bot.ledger.get_user(message.author.id)
        u["xp"] += 1
        # 30メッセージごとに自動保存
        if u["xp"] % 30 == 0:
            bot.ledger.save()
            print(f"💾 Auto-saved data for {message.author.display_name}")

    # prefixコマンド (!等) の処理
    await bot.process_commands(message)

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Error: DISCORD_BOT_TOKEN is missing in environment variables.")
