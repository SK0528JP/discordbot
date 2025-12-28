import discord
from discord import app_commands
from discord.ext import commands
import os
import aiohttp
import re
import json

class AIChat(commands.Cog):
    ai_group = app_commands.Group(name="ai", description="Rb m/25E 安定型知能中枢")

    def __init__(self, bot):
        self.bot = bot
        self.api_token = os.getenv("HUGGINGFACE_TOKEN")
        # 対話用 (Gemma: Google製の軽量・高性能モデル)
        self.chat_url = "https://api-inference.huggingface.co/models/google/gemma-1.1-7b-it"
        # 画像解析用 (BLIP: 非常に安定した画像説明モデル)
        self.vision_url = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"

    async def query_huggingface(self, url, payload):
        """APIリクエストの共通処理"""
        headers = {"Authorization": f"Bearer {self.api_token}"}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 503:
                    return "💤 AIユニットを起動中です。10秒ほど待って再試行してください。"
                if resp.status != 200:
                    res_json = await resp.json()
                    return f"⚠️ エラー ({resp.status}): {res_json.get('error', '通信失敗')}"
                return await resp.json()

    @ai_group.command(name="ask", description="AIと対話します")
    async def ask(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        if not self.api_token:
            return await interaction.followup.send("❌ HUGGINGFACE_TOKEN が未設定です。")

        # Gemma 向けの入力形式
        payload = {"inputs": f"<start_of_turn|user\n{prompt}<end_of_turn>\n<start_of_turn|model\n"}
        result = await self.query_huggingface(self.chat_url, payload)

        if isinstance(result, str):
            answer = result
        else:
            # Gemmaの応答から生成テキストを抽出
            full_text = result[0]['generated_text']
            answer = full_text.split("<start_of_turn|model\n")[-1].strip()

        await interaction.followup.send(f"🤖 **AI回答:**\n{answer[:1900]}")

    @ai_group.command(name="image", description="画像を説明します")
    async def image(self, interaction: discord.Interaction, attachment: discord.Attachment):
        await interaction.response.defer()
        if not self.api_token:
            return await interaction.followup.send("❌ トークン未設定です。")
        
        if not attachment.content_type.startswith('image/'):
            return await interaction.followup.send("❌ 画像ファイルを指定してください。")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    image_data = await resp.read()

            # BLIPモデルにバイナリデータを直接送信
            headers = {"Authorization": f"Bearer {self.api_token}"}
            async with aiohttp.ClientSession() as session:
                async with session.post(self.vision_url, headers=headers, data=image_data) as v_resp:
                    if v_resp.status == 200:
                        res = await v_resp.json()
                        description = res[0].get('generated_text', '解析できませんでした。')
                        await interaction.followup.send(f"🤖 **視覚解析結果:**\nこの画像は「{description}」のようです。")
                    elif v_resp.status == 503:
                        await interaction.followup.send("💤 視覚ユニット起動中...少し待って再試行してください。")
                    else:
                        await interaction.followup.send(f"⚠️ 解析エラー: {v_resp.status}")
        except Exception as e:
            await interaction.followup.send(f"❌ 通信失敗: {str(e)}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or self.bot.user not in message.mentions:
            return
        
        content = re.sub(f'<@!?{self.bot.user.id}>', '', message.content).strip()
        if not content: return

        async with message.channel.typing():
            payload = {"inputs": f"User: {content}\nAssistant:"}
            result = await self.query_huggingface(self.chat_url, payload)
            answer = result if isinstance(result, str) else result[0]['generated_text']
            await message.reply(answer[:2000])

async def setup(bot):
    await bot.add_cog(AIChat(bot))
