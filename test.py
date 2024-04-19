import requests

# 認証トークンをセットアップ
headers = {
    "Authorization": "Bearer secret_xc4gFpVz0om6HmZoJcS06zgzq54DkLRc0SZE3aOXJfc",
    "Content-Type": "application/json",
}

# データベースの ID をセットアップ
database_id = "3dacfb355eb34f0b9d127a988539809a"

# データベースのメタデータを取得するためのエンドポイント URL を作成
url = f"https://api.notion.com/v1/databases/{database_id}"

# メタデータを取得
response = requests.get(url, headers=headers)
print(response.json())
data = response.json()

# データベースのプロパティ一覧を取得
properties = data["properties"]

# プロパティ一覧を表示
for property_name, property_info in properties.items():
    print(property_name, "-", property_info["type"])
