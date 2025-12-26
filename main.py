import discord
from discord.ext import commands
import os
import asyncio
from ledger import Ledger

# 1. システム・データ・レジャーの初期化
# 各ユーザーの言語設定(lang)やXP、資産を管理します
ledger = Ledger()

class Rbm25Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        # システム・アイデンティティの設定
        # ステータスを「退席中(idle)」に、アクティビティを監視モードに設定
        super().__init__(
            command_prefix="!", 
            intents=intents,
            status=discord.Status.idle,
            activity=discord.Activity(
                type=discord.ActivityType.watching, 
                name="Rb m/25 System Status"
            )
        )

    async def setup_hook(self):
        """
        システムの拡張モジュール（Cogs）をロードし、
        スラッシュコマンドをグローバルに同期します。
        """
        # ロード対象のモジュール定義
        cogs_list = [
            "cogs.utility",
            "cogs.economy",
            "cogs.entertainment",
            "cogs.admin"
        ]

        for extension in cogs_list:
            try:
                # 各Cogにledgerインスタンスを渡して初期化
                # 各Cog内で user_data["lang"] を参照することで多言語化を実現します
                await self.load_extension(extension)
                print(f"[SYSTEM] Module loaded: {extension}")
            except Exception as e:
                print(f"[ERROR] Failed to load module {extension}: {e}")

        # スラッシュコマンドの同期（Discord側への反映）
        await self.tree.sync()
        print("[SYSTEM] Global command synchronization completed.")

bot = Rbm25Bot()

# --- アクティブ・ログ：貢献度(XP)蓄積ユニット ---
last_xp_time = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    now = discord.utils.utcnow()
    uid = message.author.id
    
    # スパム防止：3秒のクールタイムを設けて貢献度(XP)を付与
    if uid not in last_xp_time or (now - last_xp_time[uid]).total_seconds() > 3:
        # ledger.py内で lang フィールドの自動補完も行われます
        ledger.add_xp(uid, 2)
        ledger.save()
        last_xp_time[uid] = now

    # プレフィックスコマンド（!）の処理を継続
    await bot.process_commands(message)

# --- 起動シーケンス・ログ ---
@bot.event
async def on_ready():
    print("--------------------------------------------------")
    print(f"  Rb m/25 | Swedish Modern System Interface")
    print(f"  Status: Operational as {bot.user.name}")
    print(f"  Internal ID: {bot.user.id}")
    print("--------------------------------------------------")
    print("[LOG] Monitoring communication channels...")

# 5. システム起動
if __name__ == "__main__":
    # 環境変数からトークンを取得
    token = os.getenv("DISCORD_BOT_TOKEN")
    if token:
        bot.run(token)
    else:
        print("[CRITICAL] Token not found. System initiation aborted.")
