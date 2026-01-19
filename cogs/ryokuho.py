import discord
from discord.ext import commands
import json
import requests
from datetime import datetime, timedelta

# --- 設定項目 ---
TOKEN = 'DISCORD_BOT_TOKEN'
GITHUB_TOKEN = 'MY_GITHUB_TOKEN'
GIST_ID = 'GIST_ID'
TARGET_USER_ID = 1128950351362535456
TARGET_CHANNEL_ID = 1367349493116440639

intents = discord.Intents.default()
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Gist操作関数 ---
def load_data_from_gist():
    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        files = response.json().get('files', {})
        if 'stats.json' in files:
            content = files['stats.json']['content']
            return json.loads(content)
    # 初期データ
    return {"logs": [], "active_session": {}}

def save_data_to_gist(data):
    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    payload = {
        "files": {
            "stats.json": {
                "content": json.dumps(data, indent=4)
            }
        }
    }
    requests.patch(url, headers=headers, json=payload)

# --- ユーティリティ ---
def format_duration(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}時間{minutes}分"

def get_stats_message(user_id, current_data):
    now = datetime.now()
    # 期間の基準作成
    start_today = now.replace(hour=0, minute=0, second=0).isoformat()
    start_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0).isoformat()
    start_month = now.replace(day=1, hour=0, minute=0, second=0).isoformat()
    start_year = now.replace(month=1, day=1, hour=0, minute=0, second=0).isoformat()

    stats = {"今日": {"count": 0, "sec": 0}, "今週": {"sec": 0}, "今月": {"sec": 0}, "今年": {"sec": 0}}

    for log in current_data["logs"]:
        if log["user_id"] != user_id: continue
        
        login_at = log["login_at"]
        sec = log["duration_sec"]

        if login_at >= start_year: stats["今年"]["sec"] += sec
        if login_at >= start_month: stats["今月"]["sec"] += sec
        if login_at >= start_week: stats["今週"]["sec"] += sec
        if login_at >= start_today:
            stats["今日"]["sec"] += sec
            stats["今日"]["count"] += 1

    return (
        f"📊 **オンライン統計 (りょくほ)**\n"
        f"・本日のログイン回数: **{stats['今日']['count'] + 1}回目**\n"
        f"・今日の総オンライン時間: {format_duration(stats['今日']['sec'])}\n"
        f"・今週の合計: {format_duration(stats['今週']['sec'])}\n"
        f"・今月の合計: {format_duration(stats['今月']['sec'])}\n"
        f"・今年の合計: {format_duration(stats['今年']['sec'])}"
    )

# --- イベント ---
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_presence_update(before, after):
    if after.id != TARGET_USER_ID:
        return

    data = load_data_from_gist()
    channel = bot.get_channel(TARGET_CHANNEL_ID)

    # オンライン開始
    if before.status != discord.Status.online and after.status == discord.Status.online:
        msg = get_stats_message(after.id, data)
        data["active_session"][str(after.id)] = datetime.now().isoformat()
        save_data_to_gist(data)
        
        if channel:
            await channel.send(f"@here りょくほがオンラインになりました。\n{msg}")

    # オンライン終了
    elif before.status == discord.Status.online and after.status != discord.Status.online:
        user_key = str(after.id)
        if user_key in data["active_session"]:
            login_time_str = data["active_session"].pop(user_key)
            login_time = datetime.fromisoformat(login_time_str)
            duration = int((datetime.now() - login_time).total_seconds())
            
            data["logs"].append({
                "user_id": after.id,
                "login_at": login_time_str,
                "duration_sec": duration
            })
            # ログが増えすぎないよう、1年以上前のデータは適宜削除する処理を入れるとより安全です
            save_data_to_gist(data)

bot.run(TOKEN)
