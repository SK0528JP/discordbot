import discord
from discord.ext import commands
from discord import app_commands
import random
from typing import Optional

# --- インタラクティブ・コンポーネント：じゃんけんUI ---
class JankenView(discord.ui.View):
    def __init__(self, ledger, user_id):
        super().__init__(timeout=60)
        self.ledger = ledger
        self.user_id = user_id

    @discord.ui.button(label="Rock", style=discord.ButtonStyle.secondary, emoji="✊")
    async def rock(self, it: discord.Interaction, button: discord.ui.Button):
        await self.process_janken(it, "Rock")

    @discord.ui.button(label="Scissors", style=discord.ButtonStyle.secondary, emoji="✌️")
    async def scissors(self, it: discord.Interaction, button: discord.ui.Button):
        await self.process_janken(it, "Scissors")

    @discord.ui.button(label="Paper", style=discord.ButtonStyle.secondary, emoji="✋")
    async def paper(self, it: discord.Interaction, button: discord.ui.Button):
        await self.process_janken(it, "Paper")

    async def process_janken(self, it: discord.Interaction, user_choice):
        if it.user.id != self.user_id:
            await it.response.send_message("このセッションは他のユーザーによって開始されました。", ephemeral=True)
            return
        
        choices = ["Rock", "Scissors", "Paper"]
        bot_choice = random.choice(choices)
        
        # 判定ロジックとビジュアル設定
        if user_choice == bot_choice:
            result, color, status_msg = "Draw", 0x94a3b8, "引き分けです。もう一度挑戦できます。"
        elif (user_choice == "Rock" and bot_choice == "Scissors") or \
             (user_choice == "Scissors" and bot_choice == "Paper") or \
             (user_choice == "Paper" and bot_choice == "Rock"):
            reward = 10
            u = self.ledger.get_user(it.user.id)
            u["money"] += reward
            self.ledger.save()
            result, color, status_msg = "Victory", 0x88a096, f"おめでとうございます。インセンティブとして **{reward} 資金** を付与しました。"
        else:
            result, color, status_msg = "Defeat", 0x475569, "今回は残念な結果となりました。またの挑戦をお待ちしています。"

        embed = discord.Embed(title="Game Result", color=color)
        embed.set_author(name=f"{it.user.display_name} - Session", icon_url=it.user.display_avatar.url)
        
        # UX: 選択結果を対比させて表示
        embed.add_field(name="Your Choice", value=f"```{user_choice}```", inline=True)
        embed.add_field(name="System Choice", value=f"```{bot_choice}```", inline=True)
        embed.add_field(name="Conclusion", value=f"✨ **{result}**", inline=False)
        embed.description = status_msg
        
        embed.set_footer(text="Entertainment Simulation Module")
        
        await it.response.edit_message(content=None, embed=embed, view=None)

# --- Cog本体 ---
class Entertainment(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="janken", description="対戦シミュレーションを開始します。")
    async def janken(self, it: discord.Interaction):
        view = JankenView(self.ledger, it.user.id)
        embed = discord.Embed(
            title="Interactive Session: Rock-Paper-Scissors",
            description="手を選択してください。勝利した場合は報酬がアカウントへ反映されます。",
            color=0x94a3b8
        )
        await it.response.send_message(embed=embed, view=view)

    @app_commands.command(name="omikuji", description="本日のパーソナル診断を実行します。")
    async def omikuji(self, it: discord.Interaction):
        fortunes = [
            ("Excellent", "🌟 最高のコンディションです。積極的なアクションを推奨します。"),
            ("Good", "✅ 安定した一日となります。着実な歩みを。"),
            ("Normal", "🧘 平穏な時間です。ルーチンを大切に。"),
            ("Caution", "⚠️ 少しの休息が必要です。無理をせず、リラックスを。")
        ]
        items = ["☕ コーヒー", "📓 ノートパッド", "🍎 フレッシュフルーツ", "🍵 緑茶", "🎧 音楽"]
        
        res_title, res_desc = random.choice(fortunes)
        
        embed = discord.Embed(title="Daily Forecast", color=0x88a096)
        embed.set_author(name=f"{it.user.display_name}'s Fortune", icon_url=it.user.display_avatar.url)
        
        embed.add_field(name="Result", value=f"**{res_title}**", inline=True)
        embed.add_field(name="Lucky Item", value=random.choice(items), inline=True)
        embed.description = f"\n{res_desc}"
        
        embed.set_footer(text="Wellness Support Service")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="roulette", description="入力された項目からランダムに1つを抽出します。")
    @app_commands.describe(options="スペース区切りで選択肢を入力してください")
    async def roulette(self, it: discord.Interaction, options: str):
        choices = options.split()
        if not choices:
            await it.response.send_message("エラー：選択肢を入力してください。", ephemeral=True)
            return
        
        result = random.choice(choices)
        embed = discord.Embed(title="Decision Support", color=0x475569)
        embed.description = f"厳正な抽選の結果、以下の項目が選出されました。\n\n```\n{result}\n```"
        embed.set_footer(text="Random Selection Tool")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="comment", description="匿名でメッセージを送信します。")
    @app_commands.describe(text="メッセージ内容", image="添付画像", mode="表示形式（True: カード型 / False: テキスト型）")
    async def comment(
        self, 
        it: discord.Interaction, 
        text: str, 
        image: Optional[discord.Attachment] = None,
        mode: bool = True
    ):
        await it.response.send_message("メッセージを匿名で転送しました。", ephemeral=True)

        if mode:
            embed = discord.Embed(description=text, color=0xf1f5f9)
            embed.set_author(name="Received a new message")
            if image:
                embed.set_image(url=image.url)
            embed.set_footer(text="Anonymous Communication Channel")
            await it.channel.send(embed=embed)
        else:
            content = f"💬 **Message**\n{text}"
            if image:
                content += f"\n{image.url}"
            await it.channel.send(content=content)

async def setup(bot):
    pass
