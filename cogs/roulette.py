import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio

class Roulette(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="roulette", description="タイトルと選択肢を決めてルーレットを回します")
    @app_commands.describe(
        title="ルーレットのタイトル（例：今日の夕飯、ゲーム大会の種目）",
        options="選択肢をカンマ(,)で区切って入力してください（例：寿司,焼肉,カレー）"
    )
    async def roulette(self, it: discord.Interaction, title: str, options: str):
        """
        ユーザーが入力した選択肢からランダムに1つを選出するユニット。
        """
        # 選択肢をリストに変換（全角・半角カンマ、読点に対応）
        raw_options = options.replace("、", ",").replace(" ", ",").split(",")
        opt_list = [opt.strip() for opt in raw_options if opt.strip()]

        # 選択肢が足りない場合のチェック
        if len(opt_list) < 2:
            await it.response.send_message(
                "❌ 選択肢は2つ以上入力してください。\n入力例: `ラーメン, パスタ, うどん`", 
                ephemeral=True
            )
            return

        # 1. 開始メッセージ（演出用）
        embed = discord.Embed(
            title=f"🎡 {title} - 抽選中",
            description="ドラムロール開始！ 🥁\n\n**候補:**\n" + " | ".join([f"`{opt}`" for opt in opt_list]),
            color=0x6366f1 # インディゴ
        )
        embed.set_footer(text="Rb m/25 Entertainment Unit")
        await it.response.send_message(embed=embed)
        
        # 2. 視覚的な「待ち時間」を演出（2秒）
        await asyncio.sleep(2)

        # 3. 抽選実行
        winner = random.choice(opt_list)

        # 4. 結果表示
        result_embed = discord.Embed(
            title=f"🎡 {title} - 結果発表",
            description=(
                f"厳正なる抽選の結果...\n\n"
                f"# 🎉 **{winner}**\n\n"
                f"に決定しました！"
            ),
            color=0xf59e0b # アンバー
        )
        result_embed.set_thumbnail(url=it.user.display_avatar.url)
        result_embed.set_footer(text=f"全 {len(opt_list)} 項目の中から選出されました")
        
        # 最初のメッセージを更新して結果を表示
        await it.edit_original_response(embed=result_embed)

async def setup(bot):
    from __main__ import ledger_instance
    await bot.add_cog(Roulette(bot, ledger_instance))
