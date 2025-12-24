import os
import asyncio
import random
import json
from datetime import datetime, timezone, timedelta
from typing import Optional

import discord
from discord.ext import commands, tasks
from discord import app_commands

# ===== 基本設定 =====
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

THEME_COLOR = 0xCC0000 
DATA_FILE = "soviet_data.json"

# ===== 歴史的アーカイブ =====
QUOTES_ARCHIVE = [
    {"text": "学習し、学習し、そして学習することだ。", "author": "ウラジーミル・レーニン", "faction": "ソビエト連邦"},
    {"text": "一人の死は悲劇だが、数百万人の死は統計上の数字に過ぎない。", "author": "ヨシフ・スターリン", "faction": "ソビエト連邦"},
    {"text": "地球は青かった。", "author": "ユーリ・ガガーリン", "faction": "ソビエト連邦"},
    {"text": "汗を流せば流すほど、血を流さずに済む。", "author": "エルヴィン・ロンメル", "faction": "ドイツ"},
    {"text": "計画がその通りに進むことなど、実戦では稀である。", "author": "ヘルムート・フォン・モルトケ", "faction": "ドイツ"},
    {"text": "主は我が守りなり。", "author": "グスタフ2世アドルフ", "faction": "スウェーデン王国"},
    {"text": "信頼せよ、だが検証せよ。", "author": "ロシアのことわざ", "faction": "ソビエト連邦"}
]

# ===== Botクラス ===== 
class SovietBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!", 
            intents=intents,
            status=discord.Status.idle,
            activity=discord.Activity(type=discord.ActivityType.playing, name="🎵 労働中")
        )
        self.user_data = {}

    async def setup_hook(self):
        self.load_data()
        try:
            await self.tree.sync()
            print("--- 国家指令システム・経済改革版 同期完了 ---")
        except Exception as e:
            print(f"同期失敗: {e}")

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.user_data = json.load(f)
            except: self.user_data = {}
        else: self.user_data = {}

    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.user_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"セーブエラー: {e}")

    def get_user(self, user_id: str):
        """ユーザーデータの初期化と取得"""
        if user_id not in self.user_data:
            self.user_data[user_id] = {"xp": 0, "money": 0, "last_msg": 0}
        # 旧バージョンデータからの互換性維持
        if "money" not in self.user_data[user_id]:
            self.user_data[user_id]["money"] = 0
        return self.user_data[user_id]

    async def add_xp(self, user_id: str):
        now = datetime.now().timestamp()
        u = self.get_user(user_id)
        if now - u.get("last_msg", 0) < 5:
            return
        u["xp"] += random.randint(10, 20)
        u["last_msg"] = now
        self.save_data()

bot = SovietBot()

# ===== 経済・管理コマンド =====

@bot.tree.command(name="exchange", description="保有XPを資金($)に換金する")
@app_commands.describe(amount="換金するXP量")
async def exchange(interaction: discord.Interaction, amount: int):
    u = bot.get_user(str(interaction.user.id))
    if amount <= 0:
        await interaction.response.send_message("❌ 不正な数値だ。", ephemeral=True)
        return
    if u["xp"] < amount:
        await interaction.response.send_message(f"❌ 貢献度(XP)が不足している。現在のXP: {u['xp']}", ephemeral=True)
        return

    u["xp"] -= amount
    u["money"] += amount
    bot.save_data()
    
    embed = discord.Embed(title="☭ 国家銀行・換金証明書", color=0x00FF00)
    embed.description = f"同志 {interaction.user.mention} の貢献を資金に還元した。\n**-{amount} XP** ➔ **+${amount}**"
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="pay", description="他の同志に資金($)を送金する")
@app_commands.describe(receiver="送金相手", amount="送金額($)")
async def pay(interaction: discord.Interaction, receiver: discord.Member, amount: int):
    if receiver.bot:
        await interaction.response.send_message("❌ 機械に資金を与えても意味はない。", ephemeral=True)
        return
    if amount <= 0:
        await interaction.response.send_message("❌ 不正な送金額だ。", ephemeral=True)
        return

    sender_id = str(interaction.user.id)
    rcvr_id = str(receiver.id)
    s = bot.get_user(sender_id)
    r = bot.get_user(rcvr_id)

    if s["money"] < amount:
        await interaction.response.send_message(f"❌ 資金が不足している。保有: ${s['money']}", ephemeral=True)
        return

    s["money"] -= amount
    r["money"] += amount
    bot.save_data()

    embed = discord.Embed(title="☭ 資金移動報告書", color=THEME_COLOR)
    embed.description = f"{interaction.user.mention} から {receiver.mention} へ資金が移動された。\n通帳記載額: **${amount}**"
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="money_ranking", description="保有資金のランキングを表示する")
async def money_ranking(interaction: discord.Interaction):
    # 金額順、同値ならID順でソートを固定
    sorted_users = sorted(
        bot.user_data.items(), 
        key=lambda x: (x[1].get("money", 0), x[0]), 
        reverse=True
    )[:10]

    embed = discord.Embed(title="☭ 国家富裕層ランキング", color=0xFFD700)
    text = ""
    for i, (u_id, d) in enumerate(sorted_users):
        medal = "💰" if i == 0 else "🪙" if i <= 2 else "▫️"
        text += f"{medal} <@{u_id}>: **${d.get('money', 0)}**\n"
    
    embed.description = text if text else "記録なし"
    u = bot.get_user(str(interaction.user.id))
    embed.set_footer(text=f"あなたの保有金額: ${u['money']}")
    await interaction.response.send_message(embed=embed)

# ===== 既存コマンドの改善版 =====

@bot.tree.command(name="ranking", description="国家への貢献度(XP)ランキングを表示する")
async def ranking(interaction: discord.Interaction):
    # XP順、同値ならID順でソートを固定（結果がブレるのを防ぐ）
    sorted_users = sorted(
        bot.user_data.items(), 
        key=lambda x: (x[1].get("xp", 0), x[0]), 
        reverse=True
    )[:10]

    embed = discord.Embed(title="☭ 労働英雄ランキング", color=THEME_COLOR)
    text = ""
    for i, (u_id, d) in enumerate(sorted_users):
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"#{i+1}"
        text += f"{medal} <@{u_id}>: **{d.get('xp', 0)}** pt\n"
    
    embed.description = text if text else "労働記録なし"
    u = bot.get_user(str(interaction.user.id))
    embed.set_footer(text=f"あなたの現在の貢献度: {u['xp']} pt")
    await interaction.response.send_message(embed=embed)

# --- 以下、前回の /roulette, /comment, /meigen, /omikuji, /janken, /ping と on_message を継承 ---

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.playing, name="🎵 労働中"))
    print(f"同志 {bot.user} 経済改革を断行中。")

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.add_xp(str(message.author.id))
    await bot.process_commands(message)

# (以下、じゃんけんView等のコードは前回同様)
class JankenView(discord.ui.View):
    def __init__(self): super().__init__(timeout=60)
    async def handle_play(self, it, user_hand):
        bh = random.choice(["グー", "チョキ", "パー"])
        he = {"グー": "✊", "チョキ": "✌️", "パー": "✋"}
        if user_hand == bh: res, col = "引き分け", 0x808080
        elif ((user_hand == "グー" and bh == "チョキ") or (user_hand == "チョキ" and bh == "パー") or (user_hand == "パー" and bh == "グー")): res, col = "勝利", 0x00FF00
        else: res, col = "敗北", 0x000000
        e = discord.Embed(title="☭ 戦略的決着報告書", color=col)
        e.add_field(name="同志/国家", value=f"{he[user_hand]} vs {he[bh]}")
        e.add_field(name="判定", value=f"**{res}**", inline=False)
        for c in self.children: c.disabled = True
        await it.response.edit_message(view=self)
        await it.followup.send(embed=e)
    @discord.ui.button(label="強行突破", style=discord.ButtonStyle.danger, emoji="✊")
    async def rock(self, it, btn): await self.handle_play(it, "グー")
    @discord.ui.button(label="分断工作", style=discord.ButtonStyle.danger, emoji="✌️")
    async def sciss(self, it, btn): await self.handle_play(it, "チョキ")
    @discord.ui.button(label="包囲作戦", style=discord.ButtonStyle.danger, emoji="✋")
    async def paper(self, it, btn): await self.handle_play(it, "パー")

@bot.tree.command(name="roulette")
async def roulette(it, options: str):
    cl = options.replace("　", " ").split()
    if len(cl) < 2: return await it.response.send_message("❌ 2つ以上必要だ。", ephemeral=True)
    s = random.choice(cl)
    e = discord.Embed(title="☭ 国家意思決定", description=f"🏆 **{s}**", color=THEME_COLOR)
    await it.response.send_message(embed=e)

@bot.tree.command(name="comment")
async def comment(it, content: str, image: Optional[discord.Attachment] = None, use_embed: bool = False):
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

@bot.tree.command(name="omikuji")
async def omikuji(it):
    f = random.choice([
        {"r": "大吉", "i": "特級ウォッカ", "c": 0xFFD700},
        {"r": "中吉", "i": "ジャガイモ", "c": 0xCC0000},
        {"r": "小吉", "i": "スープ", "c": 0xCC0000},
        {"r": "末吉", "i": "塩パン", "c": 0x8B4513},
        {"r": "凶", "i": "片道切符", "c": 0x0000FF}
    ])
    e = discord.Embed(title="☭ 配給物資通達書", color=f["c"])
    e.add_field(name="判定", value=f["r"])
    e.add_field(name="支給品", value=f["i"])
    await it.response.send_message(embed=e)

@bot.tree.command(name="meigen")
async def meigen(it):
    q = random.choice(QUOTES_ARCHIVE)
    e = discord.Embed(title="📜 歴史的アーカイブ", description=f"```\n{q['text']}\n```", color=THEME_COLOR)
    e.set_footer(text=f"{q['author']} ({q['faction']})")
    await it.response.send_message(embed=e)

@bot.tree.command(name="janken")
async def janken(it):
    await it.response.send_message(embed=discord.Embed(title="☭ 戦略的決着", color=THEME_COLOR), view=JankenView())

@bot.tree.command(name="ping")
async def ping(it):
    await it.response.send_message(f"pong! {round(bot.latency*1000)}ms", ephemeral=True)

bot.run(TOKEN)
