import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai
from google.generativeai.types import RequestOptions # オプション設定用
import os
import aiohttp
import re

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # APIバージョンを v1beta ではなく v1 に強制固定
            self.request_options = RequestOptions(api_version="v1")
            # モデル名の指定から 'models/' を完全に排除、または強制
            self.model_name = "gemini-1.5-flash"
            self.model = genai.GenerativeModel(model_name=self.model_name)
        else:
            self.model = None

    async def generate_response(self, contents):
        if not self.model:
            return "❌ APIキーが未設定です。"
        
        try:
            # request_options を指定して生成を実行
            response = await self.model.generate_content_async(
                contents,
                request_options=self.request_options
            )
            
            if response and response.text:
                return response.text
            return "⚠️ 回答を生成できませんでした。"
            
        except Exception as e:
            return f"⚠️ 通信エラー: {str(e)}"

    ai_group = app_commands.Group(name="ai", description="Gemini知能中枢")

    @ai_group.command(name="ask", description="Geminiと対話します")
    async def ask(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        answer = await self.generate_response(prompt)
        await interaction.followup.send(f"🤖 **AI回答:**\n{answer[:1900]}")

    @ai_group.command(name="image", description="画像を解析します")
    async def image(self, interaction: discord.Interaction, attachment: discord.Attachment, prompt: str = "説明してください"):
        await interaction.response.defer()
        if not attachment.content_type.startswith('image/'):
            return await interaction.followup.send("❌ 画像ファイルを添付してください。")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    image_data = await resp.read()

            contents = [{"mime_type": attachment.content_type, "data": image_data}, prompt]
            answer = await self.generate_response(contents)
            await interaction.followup.send(f"🤖 **解析結果:**\n{answer[:1900]}")
        except Exception as e:
            await interaction.followup.send(f"⚠️ 解析失敗: {str(e)}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        if self.bot.user in message.mentions:
            clean_content = re.sub(f'<@!?{self.bot.user.id}>', '', message.content).strip()
            async with message.channel.typing():
                answer = await self.generate_response(clean_content)
                await message.reply(answer[:2000])

async def setup(bot):
    await bot.add_cog(AIChat(bot))
