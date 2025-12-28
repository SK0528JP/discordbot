import discord
from discord import app_commands
from discord.ext import commands
import os
import aiohttp
import re
import json

class AIChat(commands.Cog):
    ai_group = app_commands.Group(name="ai", description="Rb m/25E 統合知能中枢")

    def __init__(self, bot):
        self.bot = bot
        self.api_token = os.getenv("HUGGINGFACE_TOKEN")
        
        # 【重要】最新のルーティングURLに変更
        self.base_url = "https://router.huggingface.co/hf-inference/models"
        
        # 使用するモデルのパス
        self.chat_model = "google/gemma-1.1-7b-it"
        self.vision_model = "Salesforce/blip-image-captioning-base"

    async def query_huggingface(self, model_path, payload, is_binary=False):
        """最新のAPIエンドポイントへのリクエスト処理"""
        if not self.api_token:
            return "❌ HUGGINGFACE_TOKEN が未設定です。"

        url = f"{self.base_url}/{model_path}"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                # 画像（バイナリ）かテキスト（JSON）かで送り方を変える
                if is_binary:
                    kwargs = {"data": payload}
                else:
                    kwargs = {"json": payload}

                async with session.post(url, headers=headers, **kwargs) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 503:
                        return "💤 AIユニットを起動中です。20秒ほど待って再試行してください。"
                    elif resp.status == 410:
                        return "⚠️ APIエンドポイントが変更されました。管理者に連絡してください。"
                    else:
                        res_json = await resp.json()
                        return f"⚠️ エラー ({resp.status}): {res_json.get('error', '通信失敗')}"
        except Exception as e:
            return f"⚠️ システム障害: {str(e)}"

    @ai_group.command(name="ask", description="AIと対話します")
    async def ask(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        
        payload = {
            "inputs": f"<start_of_turn|user\n{prompt}<end_of_turn>\n<start_of_turn|model\n",
            "parameters": {"max_new_tokens": 500}
        }
        
        result = await self.query_huggingface(self.chat_model, payload)

        if isinstance(result, str):
            answer = result
        else:
            full_text = result[0]['generated_text']
            answer = full_text.split("<start_of_turn|model\n")[-1].strip()

        await interaction.followup.send(f"🤖 **AI回答:**\n{answer[:1900]}")

    @ai_group.command(name="image", description="画像を説明します")
    async def image(self, interaction: discord.Interaction, attachment: discord.Attachment):
        await interaction.response.defer()
        
        if not attachment.content_type.startswith('image/'):
            return await interaction.followup.send("❌ 画像ファイルを指定してください。")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    image_data = await resp.read()

            result = await self.query_huggingface(self.vision_model, image_data, is_binary=True)
            
            if isinstance(result, str):
                await interaction.followup.send(result)
            else:
                description = result[0].get('generated_text', '解析できませんでした。')
                await interaction.followup.send(f"🤖 **視覚解析結果:**\nこの画像は「{description}」のようです。")
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
            result = await self.query_huggingface(self.chat_model, payload)
            answer = result if isinstance(result, str) else result[0]['generated_text']
            await message.reply(answer[:2000])

async def setup(bot):
    await bot.add_cog(AIChat(bot))
