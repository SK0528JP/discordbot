import os
import asyncio
import random
import json
from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

# ===== 基本設定 =====
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DATA_FILE = "soviet_ledger.json"
THEME_COLOR = 0xCC0000

# ===== 国家元帳（データ一元管理クラス） =====
class SovietLedger:
    """
    全てのデータをメモリに保持し、非同期ロックで保護。
    不整合を物理的に排除する国家の心臓部。
    """
    def __init__(self):
        self.data = {}
        self.lock = asyncio.Lock()
        self._load()

    def _load(self):
        """起動時に一度だけファイルを読み込む"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except: self.data = {}
        else: self.data = {}

    def _save(self):
        """メモリの最新状態をファイルへ書き出す"""
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"元帳保存失敗: {e}")

    def get_user(self, user_id: str):
        """ユーザーデータの取得（なければ初期化）"""
        uid = str(user_id)
        if uid not in self.data:
            self.data[uid] = {"xp": 0, "money": 0, "last": 0}
        # 構造の健全性確保
        u = self.data[uid]
        if "xp" not in u: u["xp"] = 0
        if "money" not in u: u["money"] = 0
        if "last" not in u: u["last"] = 0
        return u

    async def add_xp(self, user_id: str):
        """1メッセージ = 2XP加算。非同期ロックで保護。"""
        uid = str(user_id)
        now = datetime.now().timestamp()
        async with self.lock:
            u = self.get_user(uid)
            # クールダウン（3秒）
            if now - u["last"] < 3:
                return
            u["xp"] += 2
            u["last"] = now
            self._save()

    async def exchange(self, user_id: str, amount: int):
        """換金処理：XPを$へ。整合性チェック付き。"""
        uid = str(user_id)
        async with self.lock:
            u = self.get_user(uid)
            if u["xp"] < amount:
                return False, u["xp"]
            u["xp"] -= amount
            u["money"] += amount
            self._save()
            return True, u["money"]

    async def transfer(self, sender_id: str, receiver_id: str, amount: int):
        """送金処理：トランザクション保護。"""
        async with self.lock:
            s = self.get_user(str(sender_id))
            r = self.get_user(str(receiver_id))
            if s["money"] < amount:
                return False
            s["money"] -= amount
            r["money"] += amount
            self._save()
            return True

ledger = SovietLedger()

# ===== Botクラス定義 =====
class SovietBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all(),
            status=discord.Status.idle, # 🌙 ステータス：退席中
            activity=discord.Activity(type=discord.ActivityType.playing, name="🎵 労働中")
        )

    async def setup_hook(self):
        await self.tree.sync()
        print("--- 国家管理システム：全デバッグ完了・稼働開始 ---")

bot = SovietBot()

# ===== イベント管理 =====
@bot.event
async def on_ready():
    # ログイン時のプレゼンス強制適用
    await bot.change_presence(
        status=discord.Status.idle, 
        activity=discord.Activity(type=discord.ActivityType.playing, name="🎵 労働中")
    )
    print(f"同志 {bot.user}、全機能をオンラインにした。時報は完全に抹消済み。")

@bot.event
async def on_message(message):
    if message.author.bot: return
    # メッセージ加算
    await ledger.add_xp(message.author.id)
    await bot.process_commands(message)

# ===== 指令コマンド群 =====

@bot.tree.command(name="status", description="自身の貢献度(XP)と保有資金($)を確認する")
async def status(it: discord.Interaction):
    u = ledger.get_user(it.user.id)
    embed = discord.Embed(title=f"☭ 同志 {it.user.display_name} の労働手帳", color=THEME_COLOR)
    embed.add_field(name="貢献度 (XP)", value=f"**{u['xp']}** pt", inline=True)
    embed.add_field(name="保有資金 ($)", value=f"**${u['money']}**", inline=True)
    embed.set_thumbnail(url=it.user.display_avatar.url)
    embed.set_footer(text="国家は君の献身を見ている。")
    await it.response.send_message(embed=embed)

@bot.tree.command(name="ranking", description="貢献度(XP)ランキングを表示")
async def ranking(it: discord.Interaction):
    # 数値(xp)でソート、同値ならID順で固定
    top = sorted(ledger.data.items(), key=lambda x: (int(x[1]['xp']), x[0]), reverse=True)[:10]
    embed = discord.Embed(title="☭ 労働英雄ランキング", color=THEME_COLOR)
    desc = "\n".join([f"🥇 <@{uid}>: **{d['xp']}** pt" for uid, d in top])
    embed.description = desc or "記録なし"
    await it.response.send_message(embed=embed)

@bot.tree.command(name="money_ranking", description="保有資金ランキングを表示")
async def money_ranking(it: discord.Interaction):
    top = sorted(ledger.data.items(), key=lambda x: (int(x[1]['money']), x[0]), reverse=True)[:10]
    embed = discord.Embed(title="☭ 国家富裕層ランキング", color=0xFFD700)
    desc = "\n".join([f"💰 <@{uid}>: **${d['money']}**" for uid, d in top])
    embed.description = desc or "記録なし"
    await it.response.send_message(embed=embed)

@bot.tree.command(name="exchange", description="XPを資金($)に換金する")
@app_commands.describe(amount="換金するXP量")
async def exchange(it: discord.Interaction, amount: int):
    if amount <= 0:
        return await it.response.send_message("❌ 不正な数値だ。", ephemeral=True)
    
    success, val = await ledger.exchange(it.user.id, amount)
    if success:
        await it.response.send_message(f"✅ 換金成功。現在の所持金: **${val}**")
    else:
        await it.response.send_message(f"❌ XPが不足している（現在: {val} XP）", ephemeral=True)

@bot.tree.command(name="pay", description="他の同志に資金を送金する")
@app_commands.describe(receiver="送金先", amount="金額")
async def pay(it: discord.Interaction, receiver: discord.Member, amount: int):
    if receiver.bot or amount <= 0:
        return await it.response.send_message("❌ 不正な操作だ。", ephemeral=True)
    
    if await ledger.transfer(it.user.id, receiver.id, amount):
        await it.response.send_message(f"💰 {it.user.mention} ➔ {receiver.mention} へ **${amount}** を送金した。")
    else:
        await it.response.send_message("❌ 資金不足だ。", ephemeral=True)

@bot.tree.command(name="roulette", description="選択肢から一つをランダムに採択する")
@app_commands.describe(options="スペース区切りで選択肢を入力")
async def roulette(it: discord.Interaction, options: str):
    cl = options.replace("　", " ").split()
    if len(cl) < 2:
        return await it.response.send_message("❌ 2つ以上の選択肢を入力せよ。", ephemeral=True)
    
    result = random.choice(cl)
    embed = discord.Embed(title="☭ 国家意思決定", description=f"厳正なる抽選の結果、以下の案が採択された。\n\n🏆 **{result}**", color=THEME_COLOR)
    embed.set_footer(text="この決定は絶対である。")
    await it.response.send_message(embed=embed)

@bot.tree.command(name="comment", description="公式声明を配信する")
@app_commands.describe(content="声明文", image="画像(任意)", use_embed="埋め込み形式")
async def comment(it: discord.Interaction, content: str, image: Optional[discord.Attachment] = None, use_embed: bool = False):
    content = content.replace("\\n", "\n")
    if use_embed:
        e = discord.Embed(description=content, color=THEME_COLOR)
        e.set_author(name="☭ 国家公式声明", icon_url=bot.user.display_avatar.url)
        if image: e.set_image(url=image.url)
        await it.channel.send(embed=e)
    else:
        f = await image.to_file() if image else None
        await it.channel.send(content=content, file=f)
    await it.response.send_message("配信完了。", ephemeral=True)

@bot.tree.command(name="ping", description="インフラ通信速度の計測")
async def ping(it: discord.Interaction):
    await it.response.send_message(f"📡 応答速度: {round(bot.latency * 1000)}ms", ephemeral=True)

bot.run(TOKEN)
