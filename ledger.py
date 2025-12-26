import json
import os
import datetime
import requests

class Ledger:
    def __init__(self, filename="ledger.json"):
        self.filename = filename
        self.github_token = os.getenv("MY_GITHUB_TOKEN")
        self.gist_id = os.getenv("GIST_ID")
        # 起動時にGistから最新データを取得、失敗したらローカルを読み込む
        self.data = self.sync_from_gist()

    def sync_from_gist(self):
        """Gistからデータをダウンロードします。"""
        if self.github_token and self.gist_id:
            try:
                url = f"https://api.github.com/gists/{self.gist_id}"
                headers = {"Authorization": f"token {self.github_token}"}
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    gist_data = response.json()
                    content = gist_data["files"][self.filename]["content"]
                    print("[SYSTEM] Data synced from Gist successfully.")
                    return json.loads(content)
            except Exception as e:
                print(f"[WARNING] Gist sync failed: {e}. Falling back to local.")
        
        return self.load_local()

    def load_local(self):
        """ローカルファイルから読み込みます。"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save(self):
        """データを保存し、Gistへアップロードします。"""
        # まずローカルに保存
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Local save failed: {e}")

        # Gistへアップロード（永続化）
        if self.github_token and self.gist_id:
            try:
                url = f"https://api.github.com/gists/{self.gist_id}"
                headers = {"Authorization": f"token {self.github_token}"}
                payload = {
                    "files": {
                        self.filename: {
                            "content": json.dumps(self.data, indent=4, ensure_ascii=False)
                        }
                    }
                }
                res = requests.patch(url, headers=headers, json=payload)
                if res.status_code == 200:
                    print("[SYSTEM] Data backed up to Gist.")
                else:
                    print(f"[ERROR] Gist update failed: {res.status_code}")
            except Exception as e:
                print(f"[ERROR] Gist sync error: {e}")

    def get_user(self, user_id):
        uid = str(user_id)
        if uid not in self.data:
            self.data[uid] = {
                "xp": 0,
                "money": 100,
                "lang": "ja",
                "joined_at": datetime.datetime.now().strftime("%Y-%m-%d"),
                "last_active": "N/A"
            }
        
        u = self.data[uid]
        if "lang" not in u: u["lang"] = "ja"
        if "money" not in u: u["money"] = 100
        if "xp" not in u: u["xp"] = 0
        return u

    def add_xp(self, user_id, amount):
        u = self.get_user(user_id)
        u["xp"] += amount
        u["last_active"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
