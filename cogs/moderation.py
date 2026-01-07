import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta, timezone

# タイムゾーン設定
JST = timezone(timedelta(hours=9), 'JST')

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # --- [DESIGNER CONFIGURATION] ---
        # あなたのユーザーIDを設定してください
        self.designer_id = 840821281838202880 

    def get_now_jst(self):
        return datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

    def is_privileged(self, it: discord.Interaction, target: discord.Member):
        """
        執行権限の判定ロジック
        1. 実行者が設計者(あなた)なら、Bot自身の役職順位のみをチェック
        2. それ以外の管理者は、自分より下の役職のみ処置可能
        """
        if it.user.id == self.designer_id:
            # 設計者の場合：Botより下の役職なら誰でもOK
            return target.top_role < it.guild.me.top_role
        else:
            # 一般管理者の場合：自分より下、かつBotより下の役職のみOK
            return target.top_role < it.user.top_role and target.top_role < it.guild.me.top_role

    mode_choices = [
        app_commands.Choice(name="🔒 自分のみ表示 (Private)", value=1),
        app_commands.Choice(name="📢 公開して表示 (Public)", value=0)
    ]

    # --- 1. BAN コマンド ---
    @app_commands.command(name="ban", description="対象ユーザーをサーバーから追放します (設計者特権対応)")
    @app_commands.describe(target="追放対象", reason="理由", mode="表示モード")
    @app_commands.choices(mode=mode_choices)
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, it: discord.Interaction, target: discord.Member, reason: str = "理由なし", mode: app_commands.Choice[int] = None):
        is_ephemeral = True if mode is None or mode.value == 1 else False
        await it.response.defer(ephemeral=is_ephemeral)

        if target.id == it.user.id:
            return await it.followup.send("❌ 自分自身を処置することはできません。")

        # 特権判定
        if not self.is_privileged(it, target):
            return await it.followup.send("❌ 権限不足: 対象者の役職が実行者またはBotと同等以上です。")

        try:
            await target.ban(reason=f"執行者: {it.user} | 理由: {reason}")
            embed = discord.Embed(title="🔨 執行報告: BAN", color=0xFF0000)
            embed.add_field(name="対象者", value=f"{target.mention} (`{target.id}`)", inline=False)
            embed.add_field(name="理由", value=reason, inline=False)
            embed.set_footer(text=f"執行時刻: {self.get_now_jst()}")
            await it.followup.send(embed=embed)
        except Exception as e:
            await it.followup.send(f"❌ 実行エラー: {e}")

    # --- 2. KICK コマンド ---
    @app_commands.command(name="kick", description="対象ユーザーをサーバーから蹴り出します (設計者特権対応)")
    @app_commands.describe(target="対象者", reason="理由", mode="表示モード")
    @app_commands.choices(mode=mode_choices)
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, it: discord.Interaction, target: discord.Member, reason: str = "理由なし", mode: app_commands.Choice[int] = None):
        is_ephemeral = True if mode is None or mode.value == 1 else False
        await it.response.defer(ephemeral=is_ephemeral)

        if not self.is_privileged(it, target):
            return await it.followup.send("❌ 権限不足: 対象者の役職制限に抵触しました。")

        try:
            await target.kick(reason=f"執行者: {it.user} | 理由: {reason}")
            embed = discord.Embed(title="👢 執行報告: KICK", color=0xFFAA00)
            embed.add_field(name="対象者", value=f"{target.mention} (`{target.id}`)", inline=False)
            embed.add_field(name="理由", value=reason, inline=False)
            embed.set_footer(text=f"執行時刻: {self.get_now_jst()}")
            await it.followup.send(embed=embed)
        except Exception as e:
            await it.followup.send(f"❌ 実行エラー: {e}")

    # --- 3. TIMEOUT コマンド ---
    @app_commands.command(name="timeout", description="対象ユーザーを一定時間、発言禁止にします (設計者特権対応)")
    @app_commands.describe(target="対象者", minutes="分数(1-40320)", reason="理由", mode="表示モード")
    @app_commands.choices(mode=mode_choices)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, it: discord.Interaction, target: discord.Member, minutes: int, reason: str = "理由なし", mode: app_commands.Choice[int] = None):
        is_ephemeral = True if mode is None or mode.value == 1 else False
        await it.response.defer(ephemeral=is_ephemeral)

        if not self.is_privileged(it, target):
            return await it.followup.send("❌ 権限不足: 対象者の役職制限に抵触しました。")
        if not (1 <= minutes <= 40320):
            return await it.followup.send("❌ 分数は1分から28日の間で指定してください。")

        try:
            duration = timedelta(minutes=minutes)
            await target.timeout(duration, reason=f"執行者: {it.user} | 理由: {reason}")
            embed = discord.Embed(title="🔇 執行報告: TIMEOUT", color=0x5E81AC)
            embed.add_field(name="対象者", value=f"{target.mention}", inline=True)
            embed.add_field(name="期間", value=f"{minutes} 分間", inline=True)
            embed.add_field(name="理由", value=reason, inline=False)
            embed.set_footer(text=f"執行時刻: {self.get_now_jst()}")
            await it.followup.send(embed=embed)
        except Exception as e:
            await it.followup.send(f"❌ 実行エラー: {e}")

    @ban.error
    @kick.error
    @timeout.error
    async def mod_error(self, it: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await it.response.send_message("❌ あなたにはこのコマンドを実行する権限がありません。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
