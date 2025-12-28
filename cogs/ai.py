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
        
        # 【重要】最新のルーティングURL。末尾にスラッシュを入れない。
        self.base_url = "https://router.huggingface.co/hf-inference/models"
        
        # モデル選定：新エンドポイントで稼働が確認されているもの
        self.chat_model = "microsoft/Phi-3-mini-4k-instruct"
        self.vision_model = "Salesforce/blip-image-captioning-base"

    async def query_api(self, model_id, payload, is_binary=False):
        if not self.api_token:
            return "❌ HUGGINGFACE_TOKEN が未設定です。"

        # 新仕様に基づいたURL構築
        url = f"{self.base_url}/{model_id}"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                if is_binary:
                    # 画像データ送信
                    async with session.post(url, headers=headers, data=payload) as resp:
                        return await self.process_response(resp)
                else:
                    # テキストデータ送信
                    async with session.post(url, headers=headers, json=payload) as resp:
                        return await self.process_response(resp)
        except Exception as e:
            return f"⚠️ 通信失敗: {str(e)}"

    async def process_response(self, resp):
        """レスポンスの共通処理。404や503を適切に捌く"""
        if resp.status == 200:
            return await resp.json()
        elif resp.status == 503:
            return "💤 AIユニット起動中... (20秒ほど待って再試行してください)"
        elif resp.status == 404:
            return f"⚠️ 404: モデル '{resp.url}' が見つかりません。パスを確認してください。"
        else:
            try:
                err_data = await resp.json()
                return f"⚠️ APIエラー ({resp.status}): {err_data.get('error', '不明')}"
            except:
                return f"⚠️ 接続失敗 ({resp.status}): サーバーが想定外の応答をしました。"

    @ai_group.command(name="ask", description="AIと対話します")
    async def ask(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        
        # Phi-3 向けのプロンプト形式
        payload = {
            "inputs": f"<|user|>\n{prompt}<|end|>\n<|assistant|>",
            "parameters": {"max_new_tokens": 500, "return_full_text": False}
        }
        
        result = await self.query_api(self.chat_model, payload)
        
        if isinstance(result, str):
            answer = result
        else:
            # 配列で返ってくるため最初の要素を取得
            answer = result[0].get('generated_text', '応答が空でした。')

        await interaction.followup.send(f"🤖 **AI回答:**\n{answer[:1900]}")

    @ai_group.command(name="image", description="画像を解析します")
    async def image(self, interaction: discord.Interaction, attachment: discord.Attachment):
        await interaction.response.defer()
        
        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            return await interaction.followup.send("❌ 画像ファイルを指定してください。")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    image_data = await resp.read()

            result = await self.query_api(self.vision_model, image_data, is_binary=True)
            
            if isinstance(result, str):
                await interaction.followup.send(result)
            else:
                desc = result[0].get('generated_text', '解析不能')
                await interaction.followup.send(f"🤖 **視覚解析:** {desc}")
        except Exception as e:
            await interaction.followup.send(f"❌ 解析失敗: {str(e)}")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
