import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone

# main.py の JST 設定と同期
JST = timezone(timedelta(hours=9), 'JST')

class Ryokuho(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 監視対象ユーザーのリスト
        self.target_user_ids = [
            1128950351362535456, # りょくほ
            719498030549696582, #sera
            1315637350772244532, #satuki
            973500097675558913, #eiki
            1105119266086342757, #ogi
            943574149048205392, #aoto
            840821281838202880, #sho
            929653926494621766, #aoba
            844162909919772683   # hiro
        ]
        self.target_channel_id = 1367349493116440639

    def format_duration(self, seconds):
        if seconds <= 0:
            return "0分"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}時間{minutes}分"

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
        # リストに含まれるユーザーかつ、ステータスの実質的な変化のみ検知
        if after.id not in self.target_user_ids or before.status == after.status:
            return

        if not self.bot.ledger:
            return

        user_data = self.bot.ledger.get_user(after.id)
        channel = self.bot.get_channel(self.target_channel_id)
        user_name = after.display_name # サーバーでの表示名を取得

        # --- [ログイン検知] ---
        if after.status == discord.Status.online:
            stats = self.calculate_stats(user_data)
            count_today = stats["今日"]["count"] + 1
            
            msg = (
                f"📊 **オンライン統計 ({user_name})**\n"
                f"・本日のログイン回数: **{count_today}回目**\n"
                f"・今日の総オンライン時間: {self.format_duration(stats['今日']['sec'])}\n"
                f"・今週の合計: {self.format_duration(stats['今週']['sec'])}\n"
                f"・今月の合計: {self.format_duration(stats['今月']['sec'])}\n"
                f"・今年の合計: {self.format_duration(stats['今年']['sec'])}"
            )
            
            user_data["active_session_start"] = datetime.now(JST).isoformat()
            
            if channel:
                await channel.send(f" {user_name} がオンラインになりました。\n{msg}")
            
            self.bot.ledger.save()

        # --- [ログアウト検知] ---
        elif before.status == discord.Status.online and after.status != discord.Status.online:
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
                    print(f"💾 [Ryokuho System] Log Saved for {user_name}: {duration}s")
                except Exception as e:
                    print(f"❌ [Ryokuho System] Error: {e}")

async def setup(bot):
    await bot.add_cog(Ryokuho(bot))
