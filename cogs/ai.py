import discord
from discord import app_commands
from discord.ext import commands
import os
import aiohttp
import re
import base64
import json

class AIChat(commands.Cog):
    # Discord上のコマンドグループ定義
    ai_group = app_commands.Group(name="ai", description="Rb m/25E 統合知能中枢 (Hugging Face)")

    def __init__(self, bot):
        self.bot = bot
        # GitHub Secretsに登録した HUGGINGFACE_TOKEN を取得
        self.api_token = os.getenv("HUGGINGFACE_TOKEN")
        # Idefics3-8B: Llama3ベースの最新マルチモーダルモデル
        self.url = "https://api-inference.huggingface.co/models/HuggingFaceM4/Idefics3-8B-Llama3"

    async def generate_response(self, prompt, image_data=None, mime_type=None):
        """Hugging Face APIへリクエストを送信するコア関数"""
        if not self.api_token:
            return "❌ Hugging Faceトークンが未設定です。GitHubのSecretsを確認してください。"

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        # モデルへの入力プロンプトを構築
        if image_data:
            # 画像がある場合はBase64形式で埋め込む
            base64_image = base64.b64encode(image_data).decode('utf-8')
            data_uri = f"data:{mime_type};base64,{base64_image}"
            # Ideficsの標準的な入力フォーマット
            inputs = f"User:![]({data_uri}){prompt}\nAssistant:"
        else:
            # テキストのみの場合
            inputs = f"User:{prompt}\nAssistant:"

        payload = {
            "inputs": inputs,
            "parameters": {
                "max_new_tokens": 500,
                "top_p": 0.9,
                "temperature": 0.7
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, headers=headers, json=payload) as resp:
                    result = await resp.json()
                    
                    if resp.status == 200:
                        # 生成されたテキストから回答部分を抽出
                        full_text = result[0]['generated_text']
                        # 'Assistant:' 以降の文字列を回答として取得
                        answer = full_text.split("Assistant:")[-1].strip()
                        return answer
                    elif resp.status == 503:
                        # 無料枠の場合、モデルがロードされるまで時間がかかることがある
                        return "💤 視覚ユニット（モデル）を起動中です... 20秒ほど待ってから再度指示を投げてください。"
                    else:
                        error_msg = result.get('error', '不明なエラー')
                        return f"⚠️ 接続エラー ({resp.status}): {error_msg}"
        except Exception as e:
            return f"⚠️ システム障害: {str(e)}"

    @ai_group.command(name="ask", description="テキストでAIと対話します")
    @app_commands.describe(prompt="質問したい内容")
    async def ask(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        answer = await self.generate_response(prompt)
        # Discordの文字数制限対策
        await interaction.followup.send(f"🤖 **AI回答:**\n{answer[:1900]}")

    @ai_group.command(name="image", description="画像を送信して解析・質問します")
    @app_commands.describe(attachment="解析する画像ファイル", prompt="画像について聞きたいこと")
    async def image(self, interaction: discord.Interaction, attachment: discord.Attachment, prompt: str = "この画像には何が写っていますか？"):
        await interaction.response.defer()
        
        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            return await interaction.followup.send("❌ 画像ファイル（png, jpgなど）を添付してください。", ephemeral=True)

        try:
            # 画像をバイトデータとしてダウンロード
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        return await interaction.followup.send("❌ 画像の取得に失敗しました。")
                    image_bytes = await resp.read()
            
            answer = await self.generate_response(prompt, image_bytes, attachment.content_type)
            await interaction.followup.send(f"🤖 **画像解析結果:**\n{answer[:1900]}")
        except Exception as e:
            await interaction.followup.send(f"❌ 解析中にエラーが発生しました: {str(e)}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """メンションへの自動応答"""
        if message.author.bot:
            return
        
        if self.bot.user in message.mentions:
            # メンション部分を削除してテキストを抽出
            content = re.sub(f'<@!?{self.bot.user.id}>', '', message.content).strip()
            if not content:
                await message.reply("📡 待機中です。何かご用でしょうか？")
                return

            async with message.channel.typing():
                answer = await self.generate_response(content)
                await message.reply(answer[:2000])

async def setup(bot):
    await bot.add_cog(AIChat(bot))
