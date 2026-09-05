import json
from datetime import datetime, timezone
from pathlib import Path

STATE_PATH = Path("memory/state.json")
OUTBOX_PATH = Path("memory/outbox.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    state = load_json(STATE_PATH)

    if state.get("wake_decision") != "candidate":
        print("💤 没有有效的自主唤醒候选")
        return

    now = datetime.now(timezone.utc)

    # 当前只是链路测试。
    # 真正接入 AI 后，这里会由模型根据最近上下文生成。
   CONTEXT_PATH = Path("memory/context.json")

    output = {
        "created_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "type": "AI_WAKE",
        "status": "pending",
        "message": message
    }

    save_json(OUTBOX_PATH, output)

    state["last_autonomous_wake"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    state["wake_count"] = state.get("wake_count", 0) + 1
    state["pending_wake"] = False
    state["status"] = "wake_generated"

    save_json(STATE_PATH, state)

    print("🌙 小家生成了一条自主消息")
    print("--------------------------------")
    print(message)
    print("--------------------------------")
    print("📦 已写入 memory/outbox.json")


if __name__ == "__main__":
    main()
