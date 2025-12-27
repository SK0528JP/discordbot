import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai
import os
import aiohttp
import re

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # モデル名のみを指定。余計なオプション（RequestOptions等）を全廃
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    async def generate_response(self, contents):
        """生成処理を最も基本的な形に集約"""
        if not self.model:
            return "❌ APIキーが未設定です。"
        
        try:
            # 最もシンプルな非同期呼び出し
            response = await self.model.generate_content_async(contents)
            
            if response and response.text:
                return response.text
            return "⚠️ 回答を生成できませんでした（安全フィルターの影響かもしれません）。"
            
        except Exception as e:
            # 404が出る場合、ここで詳細な原因を表示
            return f"⚠️ 接続エラー: {str(e)}"

    # --- /ai コマンドグループ ---
    ai_group = app_commands.Group(name="ai", description="Gemini知能中枢")

    @ai_group.command(name="ask", description="テキストで質問します")
    async def ask(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        answer = await self.generate_response(prompt)
        # Discordの2000文字制限を回避
        await interaction.followup.send(f"🤖 **AI回答:**\n{answer[:1900]}")

    @ai_group.command(name="image", description="画像を解析します")
    async def image(self, interaction: discord.Interaction, attachment: discord.Attachment, prompt: str = "この画像について説明してください"):
        await interaction.response.defer()
        if not attachment.content_type.startswith('image/'):
            return await interaction.followup.send("❌ 画像ファイルを添付してください。", ephemeral=True)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200: return await interaction.followup.send("❌ 画像取得失敗")
                    image_data = await resp.read()

            # 画像データの構成（最も標準的な形式）
            contents = [{"mime_type": attachment.content_type, "data": image_data}, prompt]
            answer = await self.generate_response(contents)
            await interaction.followup.send(f"🤖 **解析結果:**\n{answer[:1900]}")
        except Exception as e:
            await interaction.followup.send(f"⚠️ 解析エラー: {str(e)}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """メンション応答機能"""
        if message.author.bot: return
        if self.bot.user in message.mentions or (message.reference and message.reference.resolved and message.reference.resolved.author.id == self.bot.user.id):
            clean_content = re.sub(f'<@!?{self.bot.user.id}>', '', message.content).strip()
            if not clean_content: return
            async with message.channel.typing():
                answer = await self.generate_response(clean_content)
                await message.reply(answer[:2000])

async def setup(bot):
    await bot.add_cog(AIChat(bot))
