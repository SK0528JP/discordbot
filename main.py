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

class SovietLedger:
    def __init__(self):
        self.data = {}
        self.lock = asyncio.Lock()
        self._load()

    def _load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except: self.data = {}
        else: self.data = {}

    def _save(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存失敗: {e}")

    def get_user(self, user_id: str):
        uid = str(user_id)
        if uid not in self.data:
            self.data[uid] = {"xp": 0, "money": 0, "last": 0}
        # 型の安定化
        u = self.data[uid]
        u["xp"] = int(u.get("xp", 0))
        u["money"] = int(u.get("money", 0))
        return u

    async def add_xp(self, user_id: str):
        uid = str(user_id)
        now = datetime.now().timestamp()
        async with self.lock:
            u = self.get_user(uid)
            if now - u.get("last", 0) < 3:
                return
            u["xp"] += 2
            u["last"] = now
            self._save()

    async def exchange(self, user_id: str, amount: int):
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
        """送金コマンドのデバッグ済み心臓部"""
        s_uid = str(sender_id)
        r_uid = str(receiver_id)
        
        # 自己送金チェック
        if s_uid == r_uid:
            return False, "自己送金不可"

        async with self.lock:
            s = self.get_user(s_uid)
            r = self.get_user(r_uid)
            
            if s["money"] < amount:
                return False, "資金不足"
            
            # ここで一気に書き換える（トランザクション）
            s["money"] -= amount
            r["money"] += amount
            self._save()
            return True, s["money"]

ledger = SovietLedger()

class SovietBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all(),
            status=discord.Status.idle,
            activity=discord.Activity(type=discord.ActivityType.playing, name="🎵 労働中")
        )
    async def setup_hook(self):
        await self.tree.sync()

bot = SovietBot()

# ===== コマンド群（デバッグ完了） =====

@bot.tree.command(name="pay", description="他の同志に資金($)を送金する")
@app_commands.describe(receiver="送金先", amount="送金額")
async def pay(it: discord.Interaction, receiver: discord.Member, amount: int):
    if receiver.bot:
        return await it.response.send_message("❌ 機械に資金を送ることはできない。", ephemeral=True)
    if amount <= 0:
        return await it.response.send_message("❌ 正の整数を入力せよ。", ephemeral=True)

    success, result = await ledger.transfer(it.user.id, receiver.id, amount)
    
    if success:
        embed = discord.Embed(title="☭ 資金移動報告書", color=THEME_COLOR)
        embed.description = f"{it.user.mention} ➔ {receiver.mention}\n**${amount}** の送金が完了した。\n現在の所持金: **${result}**"
        await it.response.send_message(embed=embed)
    else:
        # エラー理由に応じた返答
        error_msg = "資金が不足している。" if result == "資金不足" else "自身には送金できない。"
        await it.response.send_message(f"❌ {error_msg}", ephemeral=True)

@bot.tree.command(name="status", description="自身のステータスを確認")
async def status(it: discord.Interaction):
    u = ledger.get_user(it.user.id)
    embed = discord.Embed(title=f"☭ {it.user.display_name} の労働手帳", color=THEME_COLOR)
    embed.add_field(name="貢献度(XP)", value=f"{u['xp']} pt", inline=True)
    embed.add_field(name="保有資金($)", value=f"${u['money']}", inline=True)
    await it.response.send_message(embed=embed)

@bot.tree.command(name="ranking")
async def ranking(it: discord.Interaction):
    # 数値ソートを徹底
    sorted_items = sorted(ledger.data.items(), key=lambda x: (int(x[1].get("xp", 0)), x[0]), reverse=True)[:10]
    desc = "\n".join([f"🥇 <@{uid}>: **{d['xp']}** pt" for uid, d in sorted_items])
    await it.response.send_message(embed=discord.Embed(title="☭ 労働英雄ランキング", description=desc or "記録なし", color=THEME_COLOR))

@bot.event
async def on_message(message):
    if message.author.bot: return
    await ledger.add_xp(message.author.id)
    await bot.process_commands(message)

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.playing, name="🎵 労働中"))
    print(f"同志 {bot.user}、全インフラの安定を確認。")

bot.run(TOKEN)
