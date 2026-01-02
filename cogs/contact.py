import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

class Contact(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 🚨 Bot管理者のIDを設定
        self.admin_id = 840821281838202880 

    # 宛先のオートコンプリート機能
    async def destination_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        choices = [
            app_commands.Choice(name="👑 開発者 (To Developer)", value="dev"),
        ]
        # 入力があれば、それをユーザーIDとして解釈する選択肢を追加
        if current.isdigit():
            choices.append(app_commands.Choice(name=f"👤 User ID: {current}", value=current))
        return choices

    @app_commands.command(name="contact", description="任意の相手、または開発者にDMを送信します")
    @app_commands.describe(
        destination="宛先 (ユーザーID、メンション、または 'dev' で開発者)",
        show_identity="送信者の情報を開示するか (True: 開示 / False: 匿名)",
        message="送信するメッセージ内容"
    )
    @app_commands.autocomplete(destination=destination_autocomplete)
    async def send_contact(self, it: discord.Interaction, destination: str, show_identity: bool, message: str):
        """
        指定された相手にBot経由でメッセージを送信します。
        """
        await it.response.defer(ephemeral=True)

        target_user = None

        # --- 1. 宛先の解析 (Target Analysis) ---
        # A. 開発者モード
        if destination.lower() in ["dev", "admin", "owner", "開発者", "管理者"]:
            target_user = await self.bot.fetch_user(self.admin_id)
        
        # B. ユーザー指定モード (メンション or ID)
        else:
            # <@12345...> 形式や数字のみをクリーニング
            clean_id = destination.replace("<@", "").replace(">", "").replace("!", "")
            if clean_id.isdigit():
                try:
                    target_user = await self.bot.fetch_user(int(clean_id))
                except discord.NotFound:
                    await it.followup.send("❌ 指定されたユーザーが見つかりません。", ephemeral=True)
                    return
                except discord.HTTPException:
                    await it.followup.send("❌ ユーザー情報の取得に失敗しました。", ephemeral=True)
                    return
            else:
                await it.followup.send("❌ 宛先の形式が不正です。ID、メンション、または 'dev' を入力してください。", ephemeral=True)
                return

        # Bot自身やBotへの送信を防ぐ
        if target_user.bot:
            await it.followup.send("❌ Botに対してメッセージを送ることはできません。", ephemeral=True)
            return

        # --- 2. メッセージの暗号化/構築 (Encryption & Payload) ---
        color = 0x2ecc71 if show_identity else 0x95a5a6 # 緑:実名 / グレー:匿名
        title = "📩 受信メッセージ (Incoming Transmission)"
        
        if show_identity:
            sender_name = f"{it.user.name} (ID: {it.user.id})"
            icon_url = it.user.display_avatar.url
            footer_text = f"Source: {it.guild.name if it.guild else 'DM'}"
        else:
            sender_name = "🕶️ 匿名ユーザー (Anonymous Agent)"
            icon_url = "https://cdn.discordapp.com/embed/avatars/0.png" # デフォルトアイコン
            footer_text = "Source: Unknown (Classified)"

        embed = discord.Embed(title=title, description=message, color=color, timestamp=datetime.now())
        embed.set_author(name=sender_name, icon_url=icon_url)
        embed.set_footer(text=f"Rb m/25 Relay System | {footer_text}")

        # --- 3. 送信処理 (Transmission) ---
        try:
            await target_user.send(embed=embed)
            
            # 完了通知
            dest_name = "開発者" if target_user.id == self.admin_id else target_user.name
            mode = "公開" if show_identity else "匿名"
            await it.followup.send(f"✅ **{dest_name}** へメッセージを送信しました。(モード: {mode})", ephemeral=True)
            
            # ログ出力
            print(f"📡 [CONTACT] From: {it.user.name} -> To: {dest_name} | Mode: {mode}")

        except discord.Forbidden:
            await it.followup.send(f"❌ **{target_user.name}** のDMが閉鎖されているため、送信できませんでした。", ephemeral=True)
        except Exception as e:
            await it.followup.send(f"❌ 送信中に予期せぬエラーが発生しました: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Contact(bot))
