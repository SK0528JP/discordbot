import discord
from discord.ext import commands
from discord import app_commands

class User(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="user", description="ユーザーのプロファイルを表示します (ID検索対応)")
    @app_commands.describe(target="ユーザーのメンション、またはユーザーIDを入力してください")
    async def user_info(self, it: discord.Interaction, target: str = None):
        """
        指定したユーザーの情報を表示。
        targetが未入力なら自分、IDならそのユーザーを検索。
        """
        await it.response.defer() # 外部検索に時間がかかる場合があるので「考え中」にする

        user_obj = None

        # 1. ターゲットの特定
        if target is None:
            user_obj = it.user
        else:
            # メンションからID数字だけを抽出
            clean_id = target.replace("<@", "").replace(">", "").replace("!", "")
            
            if clean_id.isdigit():
                try:
                    # まずキャッシュ(サーバー内)から探す
                    user_obj = it.guild.get_member(int(clean_id)) if it.guild else None
                    # いなければDiscord全体から取得(fetch)
                    if user_obj is None:
                        user_obj = await self.bot.fetch_user(int(clean_id))
                except Exception:
                    user_obj = None
            else:
                await it.followup.send("❌ 有効なユーザーID、またはメンションを入力してください。", ephemeral=True)
                return

        if user_obj is None:
            await it.followup.send("❌ ユーザーが見つかりませんでした。IDが正しいか確認してください。", ephemeral=True)
            return

        # 2. データの取得
        u = self.ledger.get_user(user_obj.id)
        
        # 3. Embedの作成
        embed = discord.Embed(
            title=f"👤 ユーザープロファイル",
            description=f"**{user_obj.name}** のシステム登録情報です。",
            color=0x94a3b8
        )
        
        # アバター画像のセット（プロフィール画像）
        if user_obj.display_avatar:
            embed.set_thumbnail(url=user_obj.display_avatar.url)
            # 大きな画像として見せたい場合はこちら
            # embed.set_image(url=user_obj.display_avatar.url)

        # 基本情報
        info = (
            f"**表示名**: {user_obj.display_name}\n"
            f"**ユーザーID**: `{user_obj.id}`\n"
            f"**アカウント作成日**: {user_obj.created_at.strftime('%Y-%m-%d')}"
        )
        embed.add_field(name="基本データ", value=info, inline=False)
        
        # システムデータ（Ledgerから）
        stats = (
            f"💰 **保有資産**: {u.get('money', 0):,} cr\n"
            f"✨ **貢献度 (XP)**: {u.get('xp', 0):,} XP\n"
            f"📅 **システム登録**: {u.get('joined_at', '記録なし')}"
        )
        embed.add_field(name="Rb m/25 システムデータ", value=stats, inline=False)
        
        # 管理者判定（あなたのID）
        is_admin = "✅ 管理権限あり" if user_obj.id == 840821281838202880 else "👤 一般ユーザー"
        embed.set_footer(text=f"権igen区分: {is_admin} | Rb m/25 Infrastructure")
        
        await it.followup.send(embed=embed)

async def setup(bot):
    from __main__ import ledger_instance
    await bot.add_cog(User(bot, ledger_instance))
