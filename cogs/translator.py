import discord
from discord.ext import commands
from discord import app_commands
from googletrans import Translator
import asyncio

class TranslatorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Translatorのインスタンス作成
        self.translator = Translator()
        
        # コンテキストメニュー（右クリックメニュー）の定義
        self.ctx_menu = app_commands.ContextMenu(
            name='Rb m/25E: 日本語翻訳',
            callback=self.translate_context_menu,
        )
        # アプリインストール設定 (サーバー設置 & ユーザー設置の両方)
        self.ctx_menu.installs(guild=True, user=True)
        self.ctx_menu.contexts(guild=True, dms=True, private_channels=True)

    async def cog_load(self):
        # Bot起動時にコマンドツリーに追加
        self.bot.tree.add_command(self.ctx_menu)

    async def cog_unload(self):
        # コグがアンロードされた際に削除
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)

    async def translate_context_menu(self, it: discord.Interaction, message: discord.Message):
        """メッセージを長押し/右クリックして日本語に翻訳"""
        await it.response.defer(ephemeral=True)

        # テキストがない（画像のみ等）場合は終了
        target_text = message.content
        if not target_text or target_text.strip() == "":
            return await it.followup.send("❌ 翻訳可能なテキストが検出されませんでした。", ephemeral=True)

        try:
            # 非同期実行のためにスレッドセーフな形で呼び出し（ライブラリの仕様対策）
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: self.translator.translate(target_text, dest='ja'))
            
            embed = discord.Embed(
                title="🌐 翻訳プロトコル結果",
                color=0x4C566A,
                description=f"**原文 ({result.src})**:\n```\n{target_text}\n```\n**日本語訳**:\n{result.text}"
            )
            embed.set_footer(text="Rb m/25E | 翻訳元メッセージにジャンプするには右上のリンクを使用してください")
            
            await it.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await it.followup.send(f"❌ 翻訳エラーが発生しました。\n(Google側のIP制限、または一時的な通信エラーの可能性があります)\n`{e}`", ephemeral=True)

    @app_commands.command(name="tr", description="任意のテキストを日本語に翻訳します")
    @app_commands.describe(text="翻訳したい文章")
    @app_commands.installs(guild=True, user=True)
    @app_commands.contexts(guild=True, dms=True, private_channels=True)
    async def translate_slash(self, it: discord.Interaction, text: str):
        """スラッシュコマンドでの直接翻訳"""
        await it.response.defer(ephemeral=True)
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: self.translator.translate(text, dest='ja'))
            await it.followup.send(f"**原文**: {text}\n**日本語訳**: {result.text}", ephemeral=True)
        except Exception as e:
            await it.followup.send(f"❌ エラーが発生しました: `{e}`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TranslatorCog(bot))
