import json
from datetime import datetime, timezone

path = "memory/user_activity.json"

now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

data["last_user_return"] = now
data["updated_at"] = now
data["source"] = "test"

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write("\n")

print("USER_RETURN 已模拟")
print("时间：", now)
