import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone

# JST設定
JST = timezone(timedelta(hours=9), 'JST')

class Ryokuho(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 監視対象ユーザーIDリスト
        self.target_user_ids = [
            1128950351362535456, # ryokuho
            719498030549696582,  # sera
            1315637350772244532, # satuki
            973500097675558913,  # eiki
            1105119266086342757, # ogi
            943574149048205392,  # aoto
            840821281838202880,  # sho
            929653926494621766,  # aoba
            844162909919772683   # hiro
        ]
        self.target_channel_id = 1367349493116440639

    # --- ヘルパー関数: 時間フォーマット ---
    def format_duration(self, seconds):
        if seconds <= 0: return "0分"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if hours > 0:
            return f"{hours}時間 {minutes}分"
        return f"{minutes}分"

    # --- ヘルパー関数: 端末情報の取得 ---
    def get_device_info(self, member):
        devices = []
        if member.desktop_status != discord.Status.offline:
            devices.append("💻 PC")
        if member.mobile_status != discord.Status.offline:
            devices.append("📱 スマホ")
        if member.web_status != discord.Status.offline:
            devices.append("🌐 ブラウザ")
        
        return " + ".join(devices) if devices else "不明"

    # --- ヘルパー関数: ステータスに応じた色と名前 ---
    def get_status_style(self, status):
        if status == discord.Status.online:
            return 0x43b581, "オンライン (Online)" # 緑
        elif status == discord.Status.idle:
            return 0xfaa61a, "退席中 (Idle)"       # 黄
        elif status == discord.Status.dnd:
            return 0xf04747, "取り込み中 (DnD)"   # 赤
        else:
            return 0x747f8d, "オフライン"         # グレー

    # --- 統計計算ロジック ---
    def calculate_stats(self, user_data):
        now = datetime.now(JST)
        start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        logs = user_data.get("online_logs", [])
        stats = {
            "今日": {"count": 0, "sec": 0},
            "今週": {"sec": 0},
            "今月": {"sec": 0},
            "今年": {"sec": 0}
        }

        for log in logs:
            try:
                login_at = datetime.fromisoformat(log["login_at"])
                if login_at.tzinfo is None:
                    login_at = login_at.replace(tzinfo=JST)
                
                sec = log["duration_sec"]

                if login_at >= start_year: stats["今年"]["sec"] += sec
                if login_at >= start_month: stats["今月"]["sec"] += sec
                if login_at >= start_week: stats["今週"]["sec"] += sec
                if login_at >= start_today:
                    stats["今日"]["sec"] += sec
                    stats["今日"]["count"] += 1
            except:
                continue
        return stats

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        # 監視対象外なら無視
        if after.id not in self.target_user_ids:
            return

        # ステータスが実質変わっていないなら無視 (例: online -> online でのアクティビティ変化など)
        if before.status == after.status:
            return

        # Ledgerシステムがない場合は動作しない
        if not self.bot.ledger:
            return

        user_data = self.bot.ledger.get_user(after.id)
        channel = self.bot.get_channel(self.target_channel_id)

        # ---------------------------------------------------------
        # 【活動開始検知】: オフライン -> (オンライン/退席中/取り込み中)
        # ---------------------------------------------------------
        if before.status == discord.Status.offline and after.status != discord.Status.offline:
            
            # 統計計算
            stats = self.calculate_stats(user_data)
            count_today = stats["今日"]["count"] + 1
            
            # UI情報の取得
            color, status_text = self.get_status_style(after.status)
            device_text = self.get_device_info(after)
            avatar_url = after.display_avatar.url

            # Embed作成 (UIアップグレード)
            embed = discord.Embed(
                title=f"🚀 {after.display_name} が活動を開始しました",
                description=f"現在の状態: **{status_text}**",
                color=color,
                timestamp=datetime.now(JST)
            )
            embed.set_thumbnail(url=avatar_url)
            embed.add_field(name="📱 使用端末", value=f"```\n{device_text}\n```", inline=False)
            
            # 統計情報のフィールド
            stats_text = (
                f"**今日:** {count_today}回目 / {self.format_duration(stats['今日']['sec'])}\n"
                f"**今週:** {self.format_duration(stats['今週']['sec'])}\n"
                f"**今月:** {self.format_duration(stats['今月']['sec'])}\n"
                f"**今年:** {self.format_duration(stats['今年']['sec'])}"
            )
            embed.add_field(name="⏱️ オンライン統計", value=stats_text, inline=False)
            embed.set_footer(text="Ryokuho System", icon_url=self.bot.user.display_avatar.url)

            # 開始時刻を記録
            user_data["active_session_start"] = datetime.now(JST).isoformat()

            # 送信と保存
            if channel:
                await channel.send(embed=embed) # @here はembed外につけるか、除去するか選択可能（今回は除去して上品に）
            
            self.bot.ledger.save()

        # ---------------------------------------------------------
        # 【活動終了検知】: (オンライン/退席中/取り込み中) -> オフライン
        # ---------------------------------------------------------
        elif after.status == discord.Status.offline:
            
            start_str = user_data.pop("active_session_start", None)
            
            if start_str:
                try:
                    start_dt = datetime.fromisoformat(start_str)
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=JST)
                    
                    duration = int((datetime.now(JST) - start_dt).total_seconds())
                    
                    if "online_logs" not in user_data:
                        user_data["online_logs"] = []
                    
                    user_data["online_logs"].append({
                        "login_at": start_str,
                        "duration_sec": max(0, duration)
                    })
                    
                    self.bot.ledger.save()
                    print(f"💾 [Log] {after.display_name}: {duration}秒のセッションを保存しました。")
                except Exception as e:
                    print(f"❌ [Error] ログ保存エラー: {e}")

async def setup(bot):
    await bot.add_cog(Ryokuho(bot))
